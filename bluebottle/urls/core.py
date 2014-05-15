from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static


urlpatterns = patterns('',
    # The api urls are in the / url namespace so that they're not redirected to /en/.
    url(r'^api/users/', include('bluebottle.bb_accounts.urls.api')),
    url(r'^api/bb_organizations/', include('bluebottle.bb_organizations.urls.api')),
    url(r'^api/bb_projects/', include('bluebottle.bb_projects.urls.api')),
    url(r'^api/bb_tasks/', include('bluebottle.bb_tasks.urls.api')),
    url(r'^api/geo/', include('bluebottle.geo.urls.api')),
    url(r'^api/contact/', include('bluebottle.contact.urls.api')),
    url(r'^api/news/', include('bluebottle.news.urls.api')),
    url(r'^api/pages/', include('bluebottle.pages.urls.api')),
    url(r'^api/quotes/', include('bluebottle.quotes.urls.api')),
    url(r'^api/slides/', include('bluebottle.slides.urls.api')),
    url(r'^api/utils/', include('bluebottle.utils.urls.api')),
    url(r'^api/wallposts/', include('bluebottle.wallposts.urls.api')),
    url(r'^api/metadata/', include('bluebottle.utils.urls.api')),
    url(r'^documents/', include('bluebottle.utils.urls.main')),
)


urlpatterns += patterns(
    'loginas.views',
    url(r"^login/user/(?P<user_id>.+)/$", "user_login", name="loginas-user-login"),
)

js_info_dict = {
    'packages': ('apps.bb_accounts', 'apps.bb_projects'),
}

urlpatterns += patterns(
    '',
    (r'^js$', 'django.views.i18n.javascript_catalog'),
)

# Serve django-staticfiles (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#serving-static-files-in-development
urlpatterns += staticfiles_urlpatterns()

# Serve media files (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#django.conf.urls.static.static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
