from django.urls import include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render
from django.template.context import RequestContext
from rest_framework_jwt.views import refresh_jwt_token
from bluebottle.bb_accounts.views import AxesObtainJSONWebToken, AuthView

from bluebottle.auth.views import GetAuthToken, AuthFacebookView
from bluebottle.utils.views import LoginWithView

urlpatterns = [
    re_path(
        r'^api/config',
        include('bluebottle.clients.urls.api')
    ),
    re_path(
        r'^api/redirects/?',
        include('bluebottle.redirects.urls.api')
    ),
    re_path(
        r'^api/users/',
        include('bluebottle.bb_accounts.urls.api')
    ),
    re_path(
        r'^api/categories/',
        include('bluebottle.categories.urls.api')
    ),
    re_path(
        r'^api/geo/',
        include('bluebottle.geo.urls.api')
    ),
    re_path(
        r'^api/news/',
        include('bluebottle.news.urls.api')
    ),
    re_path(
        r'^api/utils/',
        include('bluebottle.utils.urls.api')
    ),
    re_path(
        r'^api/terms/',
        include('bluebottle.terms.urls.api')
    ),
    re_path(
        r'^api/metadata/',
        include('bluebottle.utils.urls.api')
    ),

    re_path(
        r'^api/statistics/',
        include('bluebottle.statistics.urls.api')
    ),
    re_path(
        r'^api/cms/',
        include('bluebottle.cms.urls.api')
    ),
    re_path(
        r'^api/pages/',
        include('bluebottle.cms.urls.api')
    ),
    re_path(
        r'^api/initiatives',
        include('bluebottle.initiatives.urls.api')
    ),
    re_path(
        r'^api/activities',
        include('bluebottle.activities.urls.api')
    ),

    re_path(
        r'^api/time-based',
        include('bluebottle.time_based.urls.api')
    ),
    re_path(
        r'^api/deeds',
        include('bluebottle.deeds.urls.api')
    ),
    re_path(
        r'^api/deeds',
        include('bluebottle.deeds.urls.pub')
    ),
    re_path(
        r'^api/collect',
        include('bluebottle.collect.urls.api')
    ),
    re_path(
        r'^api/assignments',
        include('bluebottle.time_based.urls.old_assignments')
    ),
    re_path(
        r'^api/funding',
        include('bluebottle.funding.urls.api')
    ),
    re_path(
        r'^api/funding/pledge',
        include('bluebottle.funding_pledge.urls.api')
    ),
    re_path(
        r'^api/funding/stripe',
        include('bluebottle.funding_stripe.urls.api')
    ),
    re_path(
        r'^api/funding/vitepay',
        include('bluebottle.funding_vitepay.urls.api')
    ),
    re_path(
        r'^api/funding/flutterwave',
        include('bluebottle.funding_flutterwave.urls.api')
    ),
    re_path(
        r'^api/funding/lipisha',
        include('bluebottle.funding_lipisha.urls.api')
    ),
    re_path(
        r'^api/funding/telesom',
        include('bluebottle.funding_telesom.urls.api')
    ),
    re_path(
        r'^api/impact/',
        include('bluebottle.impact.urls.api')
    ),
    re_path(
        r'^api/segments/',
        include('bluebottle.segments.urls.api')
    ),

    re_path(
        r'^api/updates/',
        include('bluebottle.updates.urls.api')
    ),

    re_path(
        r'^api/files/',
        include('bluebottle.files.urls.api')
    ),

    re_path(
        r'^api/organizations',
        include('bluebottle.organizations.urls.api')
    ),

    # JSON Web Token based authentication for Django REST framework
    re_path(r'^api/token-auth/', AxesObtainJSONWebToken.as_view(), name='token-auth'),

    re_path(
        r'^api/auth/facebook$',
        AuthFacebookView.as_view()
    ),

    re_path(r'^api/token-auth-refresh/$', refresh_jwt_token),

    # JSON-API Web Token based authentication for Django REST framework
    re_path(r'^api/auth$', AuthView.as_view(), name='auth'),

    # Social token authorization
    re_path(
        r'^api/social/',
        include('bluebottle.social.urls.api')
    ),

    re_path(r'token/', include('bluebottle.token_auth.urls')),

    re_path(r'^api/scim/v2/', include('bluebottle.scim.urls.api')),

    re_path(
        r'^login-with/(?P<user_id>[0-9]+)/(?P<token>[0-9A-Za-z:\-_]{1,200})',
        LoginWithView.as_view(), name='login-with'
    ),

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

    re_path(
        '',
        include('social_django.urls', namespace='social')
    ),
    re_path(
        r'^api/social-login/(?P<backend>[^/]+)/$',
        GetAuthToken.as_view()
    ),

    # Needed for the self-documenting API in Django Rest Framework.
    re_path(
        r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),

    re_path(r'^', include('django.conf.urls.i18n')),
]
