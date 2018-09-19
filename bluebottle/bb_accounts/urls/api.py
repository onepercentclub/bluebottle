from django.conf.urls import url

from ..views import (
    ManageProfileDetail, UserProfileDetail, CurrentUser, UserCreate,
    PasswordReset, PasswordSet, UserVerification, UserDataExport, Logout)

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


urlpatterns = [
    url(r'^$', UserCreate.as_view(), name='user-user-create'),
    url(r'^current$', CurrentUser.as_view(), name='user-current'),
    url(r'^logout$', Logout.as_view(), name='user-logout'),
    url(r'^passwordreset$', PasswordReset.as_view(), name='password-reset'),
    url(
        r'^passwordset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        PasswordSet.as_view(), name='password-set'),
    url(r'^profiles/manage/(?P<pk>\d+)$', ManageProfileDetail.as_view(),
        name='manage-profile'),
    url(r'^profiles/(?P<pk>\d+)$', UserProfileDetail.as_view(),
        name='user-profile-detail'),
    url(r'^verification/$', UserVerification.as_view(),
        name='user-verification'),
    url(r'^export/$', UserDataExport.as_view(),
        name='user-export'),

]
