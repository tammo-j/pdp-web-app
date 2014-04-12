from django.conf.urls import patterns, url
from orders.views import categories, category_products, search_products,\
    order_products, queue_orders, queue_order_check, order_status,\
    queue_order_sign

urlpatterns = patterns('',
    url(r'^categories/$', categories),
    url(r'^categories/(\d+)/$', category_products),
    url(r'^search/$', search_products),
    url(r'^order/$', order_products),
    url(r'^status/(\d+)/$', order_status),
    url(r'^protected-queue/$', queue_orders),
    url(r'^protected-queue-check/$', queue_order_check),
    url(r'^protected-queue-sign/$', queue_order_sign)
)
