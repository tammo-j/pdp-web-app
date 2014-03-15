from django.db import models, transaction
from django.utils import timezone
from decimal import Decimal


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
        fields = ['code__icontains', 'name__icontains']
        queries = [models.Q(**{f: query}) for f in fields]
        qs = models.Q()
        for q in queries:
            qs = qs | q
        return self.filter(qs)


class Product(models.Model):
    visible = models.BooleanField(default=True, help_text='Hides product from users. Cannot be ordered.')
    name = models.CharField(max_length=128)
    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.SET_NULL, related_name='products')
    list_weight = models.IntegerField(default=0, help_text='Light products on top, equal weight in alphabetical order.')
    image = models.ImageField(upload_to='img', blank=True, null=True)
    code = models.CharField(max_length=32, blank=True, help_text='Product code shown at the desk.')
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    max_kg = models.DecimalField(max_digits=4, decimal_places=2, default=2.5, help_text='End of the selection scale.')
    step_kg = models.DecimalField(max_digits=4, decimal_places=2, default=0.1, help_text='Step of the selection scale.')
    piece_kg = models.DecimalField(max_digits=4, decimal_places=2, default=0.0, help_text='To enable ordering in pieces enter estimate on piece weight.')
    queue_min = models.DecimalField(max_digits=3, decimal_places=1, default=0.5, help_text='Estimated queue minutes for serving this product.')
    details = models.TextField(blank=True)
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
            'price_per_kg': '%0.2f' % (self.price_per_kg),
            'max_kg': '%0.2f' % (self.max_kg),
            'step_kg': '%0.2f' % (self.step_kg),
            'piece_kg': '%0.2f' % (self.piece_kg),
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
        attrs.append(u'sum=%.2f' % (self.price_per_kg))
        if self.piece_kg > 0:
            attrs.append('piece_kg=%.2f' % (self.piece_kg))
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
        items = []
        for i in self.items.all():
            items.append({
                'pk': i.pk,
                'name': i.product_name,
                'amount': '%0.2f' % (i.amount),
                'served': i.served
            })
        return {
            'pk': self.pk,
            'number': self.number,
            'left': '%0.2f' % dif,
            'items': items
        }

    def __unicode__(self):
        return '#%d [%s] %s sum=%0.2f time=%0.2f' % (self.number, self.state, str(self.created),\
                                                     self.total_price, self.queue_time)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items')
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    served = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return '%s kg=%0.2f sum=%0.2f' % (self.product_name, self.amount, self.total_price)
