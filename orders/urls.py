from django.conf.urls import patterns, url
from orders.views import categories, category_products, search_products,\
    order_products, queue_orders, queue_order_check

urlpatterns = patterns('',
    url(r'^categories/$', categories),
    url(r'^categories/(\d+)/$', category_products),
    url(r'^search/$', search_products),
    url(r'^order/$', order_products),
    url(r'^protected-queue/$', queue_orders),
    url(r'^protected-queue-check/', queue_order_check)
)
