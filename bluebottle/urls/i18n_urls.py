from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls import patterns
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailsearch.urls import frontend as wagtailsearch_frontend_urls

from bluebottle.views import HomeView

admin.autodiscover()


urlpatterns = patterns(
    '',

    url(r'^admin/cms/', include(wagtailadmin_urls)),
    url(r'^cms/search/', include(wagtailsearch_frontend_urls)),
    url(r'^cms/documents/', include(wagtaildocs_urls)),
    url(r'^cms/', include(wagtail_urls)),


    # Django Admin, docs and password reset
    url(r'^admin/password_reset/$',
        'bluebottle.auth.views.admin_password_reset',
        name='admin_password_reset'),
    url(r'^admin/password_reset/done/$',
        'django.contrib.auth.views.password_reset_done'),

    url(
        r'^admin/password_reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
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

    # Django Admin, docs and password reset
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset',
        name='admin_password_reset'),
    url(r'^admin/password_reset/done/$',
        'django.contrib.auth.views.password_reset_done'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # Other modules that need URLs exposed
    url(r'^admin/utils/tinymce/', include('tinymce.urls')),
    url(r'^admin/utils/admintools/', include('admin_tools.urls')),

    # account login/logout, password reset, and password change
    url(r'^accounts/',
        include('django.contrib.auth.urls', namespace='accounts')),


    url(r'^admin', RedirectView.as_view(url=reverse_lazy('admin:index')), name='admin-slash'),

    url(r'^', HomeView.as_view(), name='home'),

)
