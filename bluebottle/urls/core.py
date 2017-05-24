from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token


from bluebottle.auth.views import GetAuthToken


urlpatterns = [
    url(r'^api/config',
        include('bluebottle.clients.urls.api')),
    url(r'^api/redirects/?',
        include('bluebottle.redirects.urls.api')),
    url(r'^api/users/',
        include('bluebottle.bb_accounts.urls.api')),
    url(r'^api/bb_projects/',
        include('bluebottle.bb_projects.urls.api')),
    url(r'^api/fundraisers/',
        include('bluebottle.bb_fundraisers.urls.api')),
    url(r'^api/categories/',
        include('bluebottle.categories.urls.api')),
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
    url(r'^api/rewards/',
        include('bluebottle.rewards.urls.api')),

    # Homepage API urls
    url(r'^api/homepage/',
        include('bluebottle.homepage.urls.api')),
    url(r'^api/stats',
        include('bluebottle.statistics.urls.api')),
    url(r'^api/bb_projects/',
        include('bluebottle.projects.urls.api')),
    url(r'^api/cms/',
        include('bluebottle.cms.urls.api')),

    url(r'^payments_mock/',
        include('bluebottle.payments_mock.urls.core')),
    url(r'^payments_docdata/',
        include('bluebottle.payments_docdata.urls.core')),
    url(r'^payments_interswitch/',
        include('bluebottle.payments_interswitch.urls.core')),
    url(r'^payments_vitepay/',
        include('bluebottle.payments_vitepay.urls.core')),
    url(r'^payments_flutterwave/',
        include('bluebottle.payments_flutterwave.urls.core')),

    url(r'^surveys/',
        include('bluebottle.surveys.urls.core')),

    url(r'^api/suggestions/',
        include('bluebottle.suggestions.urls.api')),

    url(r'^api/votes/',
        include('bluebottle.votes.urls.api')),
    url(r'^api/surveys/',
        include('bluebottle.surveys.urls.api')),


    # Organization urls for private documents
    url(r'^documents/',
        include('bluebottle.organizations.urls.documents')),

    url(r'^api/organizations/',
        include('bluebottle.organizations.urls.api')),

    url(r'^embed/', include('bluebottle.widget.urls.core')),

    # JSON Web Token based authentication for Django REST framework
    url(r'^api/token-auth/', obtain_jwt_token, name='token-auth'),

    url(r'^api/token-auth-refresh/$', refresh_jwt_token),

    # Social token authorization
    url(r'^api/social/',
        include('bluebottle.social.urls.api')),

    url(r'token/', include('token_auth.urls')),

    # urls for payout service
    url(r'^api/projects/',
        include('bluebottle.projects.urls.api')),
    url(r'^api/payouts/',
        include('bluebottle.payouts_dorado.urls')),

    url(r'^downloads/', include('bluebottle.projects.urls.media')),
    url(r'^downloads/', include('bluebottle.bb_tasks.urls.media')),
]


# Nicely parse 500 errors so we get semantic messages in tests.
def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


# Serve django-staticfiles (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#serving-static-files-in-development
urlpatterns += staticfiles_urlpatterns()

# Serve media files (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#django.conf.urls.static.static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [

    url('', include('social.apps.django_app.urls',
                    namespace='social')),
    url(r'^api/social-login/(?P<backend>[^/]+)/$',
        GetAuthToken.as_view()),

    # Needed for the self-documenting API in Django Rest Framework.
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    url(r'^', include('django.conf.urls.i18n')),
]
