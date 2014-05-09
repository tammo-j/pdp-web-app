from django.conf.urls import patterns, include, url
from django.contrib import admin
from ui.views import search, queue, queue_tablet, search_printed

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', search),
    url(r'^printed/$', search_printed),
    url(r'^queue/$', queue),
    url(r'^queue6u3u3/$', queue_tablet),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'ui/login.html'}),
    url(r'^rest/', include('orders.urls')),
    url(r'^admin/', include(admin.site.urls))
)
