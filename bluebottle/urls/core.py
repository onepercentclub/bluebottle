from django.urls import path
from django.urls import include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render
from django.template.context import RequestContext
from rest_framework_jwt.views import refresh_jwt_token
from bluebottle.bb_accounts.views import AxesObtainJSONWebToken, AuthView

from bluebottle.utils.views import LoginWithView

urlpatterns = [
    path(
        'api/config',
        include('bluebottle.clients.urls.api')
    ),
    re_path(
        r'^api/redirects/?',
        include('bluebottle.redirects.urls.api')
    ),
    path(
        'api/users/',
        include('bluebottle.bb_accounts.urls.api')
    ),
    path(
        'api/categories/',
        include('bluebottle.categories.urls.api')
    ),
    path(
        'api/geo/',
        include('bluebottle.geo.urls.api')
    ),
    path(
        'api/news/',
        include('bluebottle.news.urls.api')
    ),
    path(
        'api/utils/',
        include('bluebottle.utils.urls.api')
    ),
    path(
        'api/terms/',
        include('bluebottle.terms.urls.api')
    ),
    path(
        'api/metadata/',
        include('bluebottle.utils.urls.api')
    ),

    path(
        'api/statistics/',
        include('bluebottle.statistics.urls.api')
    ),
    path(
        'api/content/',
        include('bluebottle.content.urls.api')
    ),
    path(
        'api/cms/',
        include('bluebottle.cms.urls.api')
    ),
    path(
        'api/pages/',
        include('bluebottle.cms.urls.api')
    ),
    path(
        'api/initiatives',
        include('bluebottle.initiatives.urls.api')
    ),
    path(
        'api/activities',
        include('bluebottle.activities.urls.api')
    ),

    path(
        'api/time-based',
        include('bluebottle.time_based.urls.api')
    ),
    path(
        'api/deeds',
        include('bluebottle.deeds.urls.api')
    ),
    path(
        'api/collect',
        include('bluebottle.collect.urls.api')
    ),
    path(
        'api/assignments',
        include('bluebottle.time_based.urls.old_assignments')
    ),
    path(
        'api/grant-management',
        include('bluebottle.grant_management.urls.api')
    ),
    path(
        'api/funding',
        include('bluebottle.funding.urls.api')
    ),
    path(
        'api/funding/pledge',
        include('bluebottle.funding_pledge.urls.api')
    ),
    path(
        'api/funding/stripe',
        include('bluebottle.funding_stripe.urls.api')
    ),
    path(
        'api/funding/vitepay',
        include('bluebottle.funding_vitepay.urls.api')
    ),
    path(
        'api/funding/flutterwave',
        include('bluebottle.funding_flutterwave.urls.api')
    ),
    path(
        'api/funding/lipisha',
        include('bluebottle.funding_lipisha.urls.api')
    ),
    path(
        'api/funding/telesom',
        include('bluebottle.funding_telesom.urls.api')
    ),
    path(
        'api/impact/',
        include('bluebottle.impact.urls.api')
    ),
    path(
        'api/segments/',
        include('bluebottle.segments.urls.api')
    ),

    path(
        'api/updates/',
        include('bluebottle.updates.urls.api')
    ),

    path(
        'api/files/',
        include('bluebottle.files.urls.api')
    ),

    path(
        'api/organizations',
        include('bluebottle.organizations.urls.api')
    ),

    # JSON Web Token based authentication for Django REST framework
    re_path(r'^api/token-auth/', AxesObtainJSONWebToken.as_view(), name='token-auth'),

    path('api/token-auth-refresh/', refresh_jwt_token),

    # JSON-API Web Token based authentication for Django REST framework
    path('api/auth', AuthView.as_view(), name='auth'),

    # So token authorization
    path(
        'api/auth/',
        include('bluebottle.auth.urls.api')
    ),

    path(
        'api/json-ld/',
        include('bluebottle.activity_pub.urls.jsonld', namespace='json-ld')
    ),

    path(
        'api/activity-links/',
        include('bluebottle.activity_links.urls.api', namespace='activity-links')
    ),

    path('token/', include('bluebottle.token_auth.urls')),

    path('api/scim/v2/', include('bluebottle.scim.urls.api')),

    re_path(
        r'^login-with/(?P<user_id>[0-9]+)/(?P<token>[0-9A-Za-z:\-_]{1,200})',
        LoginWithView.as_view(), name='login-with'
    ),

    path('.well-known/webfinger', include('bluebottle.webfinger.urls'))
]


# Nicely parse 500 errors so we get semantic messages in tests.
def handler500(request):
    response = render(
        request, '500.html', {},
        context_instance=RequestContext(request)
    )
    response.status_code = 500
    return response


# Serve django-staticfiles (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#serving-static-files-in-development
urlpatterns += staticfiles_urlpatterns()

# Serve media files (only works in DEBUG)
# https://docs.djangoproject.com/en/dev/howto/static-files/#django.conf.urls.static.static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [

    path(
        '',
        include('social_django.urls', namespace='social')
    ),

    # Needed for the self-documenting API in Django Rest Framework.
    path(
        'api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),

    path('', include('django.conf.urls.i18n')),
]
