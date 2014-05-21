from django.conf.urls import include, url, patterns
from django.contrib import admin

from bluebottle.views import HomeView

admin.autodiscover()


urlpatterns = patterns(
    '',

    # Django Admin, docs and password reset
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
    url(r'^admin/password_reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm'),
    url(r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # Other modules that need URLs exposed
    url(r'^admin/utils/taggit-autocomplete/', include('taggit_autocomplete_modified.urls')),
    url(r'^admin/utils/tinymce/', include('tinymce.urls')),
    url(r'^admin/utils/admintools/', include('admin_tools.urls')),

    # account login/logout, password reset, and password change
    url(r'^accounts/', include('django.contrib.auth.urls', namespace='accounts')),

    url(r'^([a-zA-Z0-9\-\_]*)', HomeView.as_view(), name='home'),
)
