from django.conf.urls import url

from bluebottle.bb_accounts.views import UserActivityDetail
from bluebottle.bb_accounts.views import (
    ManageProfileDetail, UserProfileDetail, CurrentUser, UserCreate,
    PasswordReset, PasswordResetConfirm, UserVerification, UserDataExport, EmailSetView,
    PasswordSetView, TokenLogin, Logout, MemberDetail, SignUpToken,
    SignUpTokenConfirmation, CaptchaVerification,
    PasswordStrengthDetail,
)

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
    url(r'^signup-token$', SignUpToken.as_view(), name='user-signup-token'),
    url(r'^signup-token/confirm$', SignUpTokenConfirmation.as_view(), name='user-signup-token-confirm'),
    url(r'^$', UserCreate.as_view(), name='user-user-create'),
    url(r'^current/?$', CurrentUser.as_view(), name='user-current'),
    url(r'^captcha$', CaptchaVerification.as_view(), name='captcha-verification'),
    url(r'^activities/$', UserActivityDetail.as_view(), name='user-activity'),
    url(r'^email$', EmailSetView.as_view(), name='user-set-email'),
    url(r'^password$', PasswordSetView.as_view(), name='user-set-password'),
    url(r'^logout$', Logout.as_view(), name='user-logout'),
    url(r'^passwordreset$', PasswordReset.as_view(), name='password-reset'),
    url(r'^passwordreset/confirm$', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
    url(r'^member/(?P<pk>\d+)$', MemberDetail.as_view(), name='member-detail'),
    url(r'^profiles/manage/(?P<pk>\d+)$', ManageProfileDetail.as_view(),
        name='manage-profile'),
    url(r'^profiles/(?P<pk>\d+)$', UserProfileDetail.as_view(),
        name='user-profile-detail'),
    url(r'^tokenlogin$', TokenLogin.as_view(), name='token-login'),
    url(r'^verification/$', UserVerification.as_view(),
        name='user-verification'),
    url(r'^export/$', UserDataExport.as_view(),
        name='user-export'),
    url(r'^password-strength$', PasswordStrengthDetail.as_view(),
        name='password-strength'),
]
