from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static


urlpatterns = patterns('',
    # The api urls are in the / url namespace so that they're not redirected to /en/.
    url(r'^api/users/', include('bluebottle.bb_accounts.urls.api')),
    url(r'^api/metadata/', include('bluebottle.utils.urls.api')),
    url(r'^documents/', include('bluebottle.utils.urls.main')),
)

for app in settings.INSTALLED_APPS:
    if app[:11] == 'bluebottle.':
        app = app[11:]
        if app not in ['common', 'bb_accounts', 'contentplugins', 'admin_dashboard']:
            urlpatterns += patterns('',
                url(r'^api/%s/' % app, include('bluebottle.%s.urls.api' % app)),
            )


urlpatterns += patterns('loginas.views',
    url(r"^login/user/(?P<user_id>.+)/$", "user_login", name="loginas-user-login"),
)

js_info_dict = {
    'packages': ('apps.bb_accounts', 'apps.bb_projects'),
}

urlpatterns += patterns('',
    (r'^js$', 'django.views.i18n.javascript_catalog'),
)

# Serve django-staticfiles (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#serving-static-files-in-development
urlpatterns += staticfiles_urlpatterns()

# Serve media files (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#django.conf.urls.static.static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
