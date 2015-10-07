from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from bluebottle.auth.views import GetAuthToken


urlpatterns = patterns('',
                       # The api urls are in the / url namespace so that
                       # they're not redirected to /en/.
                       url(r'^api/users/',
                           include('bluebottle.bb_accounts.urls.api')),
                       url(r'^api/bb_organizations/',
                           include('bluebottle.bb_organizations.urls.api')),
                       url(r'^api/bb_projects/',
                           include('bluebottle.bb_projects.urls.api')),
                       url(r'^api/fundraisers/',
                           include('bluebottle.bb_fundraisers.urls.api')),
                       url(r'^api/bb_tasks/',
                           include('bluebottle.bb_tasks.urls.api')),
                       url(r'^api/geo/', include('bluebottle.geo.urls.api')),
                       url(r'^api/contact/',
                           include('bluebottle.contact.urls.api')),
                       url(r'^api/news/', include('bluebottle.news.urls.api')),
                       url(r'^api/pages/',
                           include('bluebottle.pages.urls.api')),
                       url(r'^api/quotes/',
                           include('bluebottle.quotes.urls.api')),
                       url(r'^api/slides/',
                           include('bluebottle.slides.urls.api')),
                       url(r'^api/utils/',
                           include('bluebottle.utils.urls.api')),
                       url(r'^api/wallposts/',
                           include('bluebottle.wallposts.urls.api')),
                       url(r'^api/terms/',
                           include('bluebottle.terms.urls.api')),
                       url(r'^api/metadata/',
                           include('bluebottle.utils.urls.api')),

                       url(r'^api/orders/',
                           include('bluebottle.bb_orders.urls.api')),
                       url(r'^api/donations/',
                           include('bluebottle.bb_donations.urls.api')),
                       url(r'^api/order_payments/', include(
                           'bluebottle.payments.urls.order_payments_api')),
                       url(r'^api/payments/',
                           include('bluebottle.payments.urls.api')),
                       url(r'^api/monthly_donations/',
                           include('bluebottle.recurring_donations.urls.api')),

                       url(r'^api/partners/',
                           include('bluebottle.partners.urls.api')),

                       # Homepage API urls
                       url(r'^api/homepage/',
                           include('bluebottle.homepage.urls.api')),
                       url(r'^api/stats',
                           include('bluebottle.statistics.urls.api')),
                       url(r'^api/bb_projects/',
                           include('bluebottle.projects.urls.api')),

                       url(r'^payments_mock/',
                           include('bluebottle.payments_mock.urls.core')),
                       url(r'^payments_docdata/',
                           include('bluebottle.payments_docdata.urls.core')),

                       # Urls for partner sites
                       url(r'^pp/',
                           include('bluebottle.partners.urls.partners')),

                       # Project view that search engines will use.
                       url(r'^projects/',
                           include('bluebottle.projects.urls.seo')),
                       url(r'^api/organizations/',
                           include('bluebottle.organizations.urls.api')),
                       url(r'^api/suggestions/',
                           include('bluebottle.suggestions.urls.api')),

                       url(r'^api/votes/',
                           include('bluebottle.votes.urls.api')),

                       # Organization urls for private documents
                       url(r'^documents/',
                           include('bluebottle.organizations.urls.documents')),

                       # handlebar templates
                       url(r'^templates/',
                           include('bluebottle.hbtemplates.urls')),

                       url(r'^embed/', include('bluebottle.widget.urls.core')),

                       # JSON Web Token based authentication for Django REST framework
                       url(r'^api/token-auth/',
                           'rest_framework_jwt.views.obtain_jwt_token'),

                       # Social token authorization
                       url(r'^api/social/',
                           include('bluebottle.social.urls.api')),

                       url(r'token/', include('token_auth.urls')),

                       )


# Nicely parse 500 errors so we get semantic messages in tests.
def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


urlpatterns += patterns(
    'loginas.views',
    url(r"^login/user/(?P<user_id>.+)/$", "user_login",
        name="loginas-user-login"),
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

urlpatterns += patterns('',

                        url('', include('social.apps.django_app.urls',
                                        namespace='social')),
                        url(r'^api/social-login/(?P<backend>[^/]+)/$',
                            GetAuthToken.as_view()),

                        # Needed for the self-documenting API in Django Rest Framework.
                        url(r'^api-auth/', include('rest_framework.urls',
                                                   namespace='rest_framework')),

                        # JSON Web Token based authentication for Django REST framework
                        url(r'^api/token-auth/',
                            'rest_framework_jwt.views.obtain_jwt_token'),
                        url(r'^api/token-auth-refresh/$',
                            'rest_framework_jwt.views.refresh_jwt_token'),

                        url(r'^', include('django.conf.urls.i18n')),
                        )

urlpatterns += patterns('loginas.views',
                        url(r"^login/user/(?P<user_id>.+)/$", "user_login",
                            name="loginas-user-login"),
                        )

js_info_dict = {
    'packages': ('apps.accounts', 'bluebottle.projects'),
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
