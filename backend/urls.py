from django.conf.urls import patterns, include, url
from django.contrib import admin
from ui.views import search, ticket, queue

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', search),
    url(r'^ticket/$', ticket),
    url(r'^queue/$', queue),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'ui/login.html'}),
    url(r'^rest/', include('orders.urls')),
    url(r'^admin/', include(admin.site.urls))
)
