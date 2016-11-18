from django.conf.urls import include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

from bluebottle.views import HomeView
from bluebottle.auth.views import admin_password_reset
from django.contrib.auth.views import password_reset_done, password_reset_confirm

admin.autodiscover()


urlpatterns = [

    # Django Admin, docs and password reset
    url(r'^admin/password_reset/$',
        admin_password_reset,
        name='admin_password_reset'),
    url(r'^admin/password_reset/done/$',
        password_reset_done, name='password_reset_done'),
    url(r'^admin/', include('loginas.urls')),
    url(
        r'^admin/password_reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        name='password_reset_confirm'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/exportdb/', include('exportdb.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # Other modules that need URLs exposed
    url(r'^admin/accounting/', include('bluebottle.accounting.urls')),

    url(r'^admin/utils/tinymce/', include('tinymce.urls')),
    url(r'^admin/utils/admintools/', include('admin_tools.urls')),

    url(r'^admin/documents/', include('bluebottle.utils.urls.main')),

    # account login/logout, password reset, and password change
    url(r'^accounts/',
        include('django.contrib.auth.urls', namespace='accounts')),

    url(r'^admin', RedirectView.as_view(url=reverse_lazy('admin:index')), name='admin-slash'),

    url(r'^', HomeView.as_view(), name='home'),

]
