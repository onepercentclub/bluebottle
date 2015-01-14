from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter

from ..views import (
    UserProfileDetail, CurrentUser, UserSettingsDetail, UserCreate,
    PasswordReset, PasswordSet, DisableAccount)

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


urlpatterns = patterns(
    '',
    url(r'^$', UserCreate.as_view(), name='user-user-create'),
    url(r'^disable-account/(?P<user_id>\d+)/(?P<token>[0-9A-Za-z]+)/$', DisableAccount.as_view(), name='disable-account'),
    url(r'^current$', CurrentUser.as_view(), name='user-current'),
    url(r'^passwordreset$', PasswordReset.as_view(), name='password-reset'),
    url(r'^passwordset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        PasswordSet.as_view(), name='password-set'),
    url(r'^profiles/(?P<pk>\d+)$', UserProfileDetail.as_view(),
        name='user-profile-detail'),
    url(r'^settings/(?P<pk>\d+)$', UserSettingsDetail.as_view(),
        name='user-settings-detail'),
)
