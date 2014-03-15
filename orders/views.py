from django.shortcuts import get_object_or_404
from django.http.response import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from orders.models import Category, Product, Order, OrderItem
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

    print request.POST

    # Parse products and amounts from POST.
    order_data = []
    total_order = Decimal(0)
    queue_time = Decimal(0)
    i = 0
    while ('product' + str(i)) in request.POST and ('amount' + str(i)) in request.POST:
        product = Product.objects.filter(pk=request.POST['product' + str(i)]).first()
        if product:
            amount = Decimal(request.POST['amount' + str(i)])
            total_product = amount * product.price_per_kg
            total_order += total_product
            queue_time += product.queue_min
            if amount > 0:
                order_data.append({'product': product, 'amount': amount, 'total': total_product })
        i += 1

    # Store to database.
    if len(order_data) > 0:
        order = Order.objects.pick()
        for data in order_data:
            order.items.create(product=data['product'], product_name=data['product'].name,\
                               amount=data['amount'], total_price=data['total'])
        order.total_price = total_order
        order.queue_time = queue_time
        wait_time = order.queue_wait_time() + queue_time
        order.estimated = order.created + timedelta(minutes=int(math.ceil(wait_time)))
        order.save()
        return _json_response({'ok':True, 'number':order.number,
                               'time':'%0.2f' % wait_time});
    
    return _json_response({'ok':False})

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
        if item:
            item.served = True
            item.save()
            order = item.order
            if order.items.filter(served=False).count() > 0:
                return _json_response({'ok':True, 'item':item.pk, 'complete':False})
            else:
                order.state = Order.SERVED
                order.save()
                return _json_response({'ok':True, 'item':item.pk, 'complete':True, 'order':order.pk})
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
