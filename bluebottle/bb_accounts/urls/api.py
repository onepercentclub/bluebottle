from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter

from ..views import (
    UserProfileDetail, CurrentUser, UserSettingsDetail, UserCreate,
    UserActivate, PasswordReset, PasswordSet, TimeAvailableViewSet)

# Public User API:
#
# User Create (POST):           /users/
# User Detail (GET/PUT):        /users/profiles/<pk>
# User Activate (GET):          /users/activate/<activation_key>
# User Password Reset (PUT):    /users/passwordreset
# User Password Set (PUT):      /users/passwordset/<uid36>-<token>
#
# Authenticated User API:
#
# Logged in user (GET):            /users/current
# User settings Detail (GET/PUT):  /users/settings/<pk>

router = DefaultRouter()
router.register(r'', TimeAvailableViewSet)

urlpatterns = patterns(
    '',
    url(r'^time_available', include(router.urls)),
    url(r'^$', UserCreate.as_view(), name='user-user-create'),
    url(r'^activate/(?P<activation_key>[a-f0-9]{40})$', UserActivate.as_view()),
    url(r'^current$', CurrentUser.as_view(), name='user-current'),
    url(r'^passwordreset$', PasswordReset.as_view(), name='password-reset'),
    url(r'^passwordset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        PasswordSet.as_view(), name='password-set'),
    url(r'^profiles/(?P<pk>\d+)$', UserProfileDetail.as_view(),
        name='user-profile-detail'),
    url(r'^settings/(?P<pk>\d+)$', UserSettingsDetail.as_view(),
        name='user-settings-detail'),
)
