from django.db import models, transaction
from django.utils import timezone
from decimal import Decimal
from django.utils.timezone import localtime


class Category(models.Model):
    visible = models.BooleanField(default=True, help_text='Hides category from users. Products are still searchable.')
    name = models.CharField(max_length=64)
    list_weight = models.IntegerField(default=0, help_text='Light categories on top, equal weight in alphabetical order.')
    image = models.ImageField(upload_to='img', blank=True, null=True)

    class Meta:
        ordering = ['-visible', 'list_weight', 'name']

    def json_fields(self):
        return {
            'pk': self.pk,
            'name': self.name,
            'image': self.image.url
        }

    def __unicode__(self):
        if self.visible:
            return self.name
        return '(hidden) %s' % (self.name)


class ProductManager(models.Manager):

    def search(self, query):
        fields = ['code__icontains', 'name__icontains', 'category__name__icontains']
        qws = models.Q()
        for word in query.split():
            queries = [models.Q(**{f: word}) for f in fields]
            qs = models.Q()
            for q in queries:
                qs = qs | q
            qws = qws & qs
        return self.filter(qws)


class Product(models.Model):
    visible = models.BooleanField(default=True, help_text='Hides product from users. Cannot be ordered.')
    name = models.CharField(max_length=128)
    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.SET_NULL, related_name='products')
    list_weight = models.IntegerField(default=0, help_text='Light products on top, equal weight in alphabetical order.')
    image = models.ImageField(upload_to='img', blank=True, null=True)
    code = models.CharField(max_length=32, blank=True, help_text='Product code shown at the desk.')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit_label = models.CharField(max_length=8, default="kg")
    scale_end = models.DecimalField(max_digits=4, decimal_places=2, default=2.5, help_text='End of the selection scale.')
    scale_step = models.DecimalField(max_digits=4, decimal_places=2, default=0.1, help_text='Step of the selection scale.')
    queue_min = models.DecimalField(max_digits=3, decimal_places=1, default=0.5, help_text='Estimated queue minutes for serving this product.')
    details = models.TextField(blank=True, help_text="Label|Value<br />Another Label|And value<br />---<br />Table Title<br />---<br />Ingredient|1 g|1%<br />---<br />* Table caption.")
    objects = ProductManager()

    class Meta:
        ordering = ['-visible', 'category', 'list_weight', 'name']

    def json_fields(self):
        return {
            'pk': self.pk,
            'name': self.name,
            'category_pk': self.category.pk,
            'category_name': self.category.name,
            'image': self.image.url,
            'code': self.code,
            'price_per_unit': '%0.2f' % (self.price_per_unit),
            'unit_label': self.unit_label,
            'scale_end': '%0.2f' % (self.scale_end),
            'scale_step': '%0.2f' % (self.scale_step),
            'details': self.details
        }

    def __unicode__(self):
        attrs = [self.name]
        if self.category:
            attrs.append('(%s)' % (self.category))
        else:
            attrs.append('(-no category-)')
        if self.code:
            attrs.append('code=%s' % (self.code))
        attrs.append(u'price=%.2f/%s' % (self.price_per_unit, self.unit_label))
        if self.visible:
            return ' '.join(attrs)
        return '(hidden) ' + ' '.join(attrs)


class OrderManager(models.Manager):

    def pick(self):
        new_order = None
        with transaction.atomic():
            order = self.filter(state=Order.QUEUED).order_by('number').first()
            if not order or order.number > 80:
                new_order = Order(number=1)
            else:
                order = self.filter(state=Order.QUEUED).order_by('-number').first()
                new_order = Order(number=order.number + 1)
            new_order.save()
        return new_order


class Order(models.Model):
    QUEUED = 'queued'
    SERVED = 'served'
    CANCELED = 'canceled'
    STATE_CHOICES = (
        (QUEUED, 'Queued for serving'),
        (SERVED, 'Served to customer'),
        (CANCELED, 'Canceled')
    )
    number = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    estimated = models.DateTimeField(blank=True, null=True)
    queue_time = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default=QUEUED)
    objects = OrderManager()

    class Meta:
        ordering = ['-state', 'created']

    def queue_wait_time(self):
        time = Decimal(0)
        for order in Order.objects.filter(state=Order.QUEUED, created__lte=self.created):
            time += order.queue_time
        return time

    def json_fields(self):
        now = timezone.now()
        dif = 0
        if self.estimated > now:
            dif = (self.estimated - now).seconds / 60
        else:
            dif = (now - self.estimated).seconds / -60
        items = {}
        for i in self.items.all():
            unit = ''
            price = 0
            code = False
            if i.product != None:
                unit = i.product.unit_label
                price = i.product.price_per_unit
                code = i.product.code
            items[i.pk] = {
                'pk': i.pk,
                'name': i.product_name,
                'code': code,
                'amount': '%0.2f %s' % (i.amount, unit),
                'price': '%0.2f' % (i.amount * price),
                'state': i.state
            }
        return {
            'pk': self.pk,
            'number': self.number,
            'estimated': localtime(self.estimated).strftime('%H:%M'),
            'left': '%0.2f' % dif,
            'items': items,
            'count': len(items),
            'state': self.state
        }

    def __unicode__(self):
        return '#%d [%s] %s sum=%0.2f time=%0.2f' % (self.number, self.state, str(self.created),\
                                                     self.total_price, self.queue_time)


class OrderItem(models.Model):
    QUEUED = 'queued'
    PACKED = 'packed'
    CANCELED = 'canceled'
    STATE_CHOICES = (
        (QUEUED, 'Queued'),
        (PACKED, 'Packed'),
        (CANCELED, 'Canceled')
    )
    order = models.ForeignKey(Order, related_name='items')
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default=QUEUED)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return '%s kg=%0.2f sum=%0.2f' % (self.product_name, self.amount, self.total_price)


class Setting(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    value = models.CharField(max_length=32)

    def __unicode__(self):
        return '%s = %s' % (self.name, self.value)
