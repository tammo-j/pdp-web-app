from django.shortcuts import get_object_or_404
from django.http.response import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from orders.models import Category, Product, Order, OrderItem, Setting
from json import dumps
from decimal import Decimal
from datetime import timedelta
import math


def categories(request):
    return _json_response_objects(Category.objects.filter(visible=True))


def category_products(request, category_pk):
    category = get_object_or_404(Category, visible=True, pk=category_pk)
    return _json_response_objects(category.products.filter(visible=True))


def search_products(request):
    if 'q' in request.GET:
        return _json_response_objects(Product.objects.search(request.GET['q']))
    return _json_response({})


def order_products(request):
    if request.method != 'POST':
        raise Http404()

    order_data = []
    total_order = Decimal(0)
    queue_time = Decimal(0)

    # Base time from settings.
    t = Setting.objects.filter(name='queue_base_time').first()
    if t != None:
        queue_time = Decimal(t.value)

    # Parse products and amounts from POST.
    i = 0
    while ('product' + str(i)) in request.POST and ('amount' + str(i)) in request.POST:
        product = Product.objects.filter(pk=request.POST['product' + str(i)]).first()
        if product:
            amount = Decimal(request.POST['amount' + str(i)])
            total_product = amount * product.price_per_unit
            total_order += total_product
            queue_time += product.queue_min
            if amount > 0:
                order_data.append({'product': product, 'amount': amount, 'total': total_product })
        i += 1

    # Store to database.
    if len(order_data) > 0:
        order = Order.objects.pick()
        for data in order_data:
            order.items.create(product=data['product'], product_name=data['product'].name, \
                               amount=data['amount'], total_price=data['total'])
        order.total_price = total_order
        order.queue_time = queue_time
        wait_time = order.queue_wait_time() + queue_time
        order.estimated = order.created + timedelta(minutes=int(math.ceil(wait_time)))
        order.save()
        return _json_response({'ok':True, 'number':order.number,
                               'estimated': localtime(order.estimated).strftime('%H:%M'),
                               'time':'%0.2f' % wait_time, 'pk':order.pk});

    return _json_response({'ok':False})


def order_status(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    return _json_response(order.json_fields())


@login_required
def queue_orders(request):
    orders = Order.objects.filter(state=Order.QUEUED)
    return _json_response_objects(orders, True)


@login_required
def queue_order_check(request):
    if request.method != 'POST':
        raise Http404()
    if 'item' in request.POST:
        item = OrderItem.objects.filter(pk=request.POST['item']).first()
        return_to_queue = False
        if item:
            if 'cancel' in request.POST and request.POST['cancel'] == 'true':
                if item.state != OrderItem.CANCELED:
                    item.state = OrderItem.CANCELED
                else:
                    item.state = OrderItem.QUEUED
                    return_to_queue = True
            else:
                if item.state != OrderItem.PACKED:
                    item.state = OrderItem.PACKED
                else:
                    item.state = OrderItem.QUEUED
                    return_to_queue = True
            item.save()
            order = item.order
            if return_to_queue:
                return _json_response({'ok':True, 'item':item.pk, 'complete':False, 'queued':True, 'order':order.pk})
            if order.items.filter(state=OrderItem.QUEUED).count() > 0:
                return _json_response({'ok':True, 'item':item.pk, 'complete':False, 'order':order.pk})
            else:
                #order.state = Order.SERVED
                #order.save()
                return _json_response({'ok':True, 'item':item.pk, 'complete':True, 'order':order.pk})
    return _json_response({'ok':False})


@login_required
def queue_order_sign(request):
    if request.method != 'POST':
        raise Http404()
    if 'order' in request.POST:
        order = Order.objects.filter(pk=request.POST['order']).first()
        if order and order.items.filter(state=OrderItem.QUEUED).count() == 0:
            order.state = Order.SERVED
            order.save()
            return _json_response({'ok':True, 'order':order.pk, 'number':order.number,
                               'estimated': localtime(order.estimated).strftime('%H:%M')})
    return _json_response({'ok':False})


@csrf_exempt
def register_print_url(request):
    PRINTER_KEY = 'printer'
    PRINTER_ADMIN_KEY = 'printer_admin'
    if PRINTER_KEY in request.POST:
        key = PRINTER_KEY

        # Detect admin printer.
        if 'location' in request.POST and request.POST['location'] == 'admin':
            key = PRINTER_ADMIN_KEY
        
        # Save to settings.
        setting = Setting.objects.filter(name=key).first()
        if setting is None:
            setting = Setting(name=key)
        setting.value = request.POST[PRINTER_KEY]
        setting.save()
        return _json_response({'ok':True})
    return _json_response({'ok':False})


def _json_response_objects(objects, array_flag=False):
    data = None
    if array_flag:
        data = []
        for o in objects:
            data.append(o.json_fields())
    else:
        data = {}
        for o in objects:
            data[o.pk] = o.json_fields()
    return _json_response(data)


def _json_response(data):
    return HttpResponse(dumps(data), content_type="application/json")
