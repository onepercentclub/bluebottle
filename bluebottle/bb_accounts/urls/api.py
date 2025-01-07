
from django.urls import re_path
from bluebottle.bb_accounts.views import UserActivityDetail, OldUserActivityDetail
from bluebottle.bb_accounts.views import (
    UserProfileDetail, CurrentUser, CurrentMemberDetail, UserCreate,
    PasswordReset, PasswordResetConfirm, UserVerification, UserDataExport, EmailSetView,
    PasswordSetView, TokenLogin, Logout, MemberDetail, SignUpToken,
    SignUpTokenConfirmation, CaptchaVerification,
    PasswordStrengthDetail, MemberSignUp,
    MemberProfileDetail, AvatarImage
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
    re_path(r'^signup-token$', SignUpToken.as_view(), name='user-signup-token'),
    re_path(r'^signup-token/confirm$', SignUpTokenConfirmation.as_view(), name='user-signup-token-confirm'),
    re_path(r'^$', UserCreate.as_view(), name='user-user-create'),
    re_path(r'^current/?$', CurrentUser.as_view(), name='user-current'),
    re_path(r'^captcha$', CaptchaVerification.as_view(), name='captcha-verification'),
    re_path(r'^activities/$', OldUserActivityDetail.as_view(), name='old-user-activity'),
    re_path(r'^user-activities/$', UserActivityDetail.as_view(), name='user-activity'),
    re_path(r'^email$', EmailSetView.as_view(), name='user-set-email'),
    re_path(r'^password$', PasswordSetView.as_view(), name='user-set-password'),
    re_path(r'^logout$', Logout.as_view(), name='user-logout'),
    re_path(r'^passwordreset$', PasswordReset.as_view(), name='password-reset'),
    re_path(r'^passwordreset/confirm$', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
    re_path(r'^members/?$', MemberSignUp.as_view(), name='member-signup'),
    re_path(r'^member/current$', CurrentMemberDetail.as_view(), name='current-member-detail'),
    re_path(r'^member/profile/(?P<pk>\d+)$', MemberProfileDetail.as_view(), name='member-profile-detail'),
    re_path(r'^member/(?P<pk>\d+)$', MemberDetail.as_view(), name='member-detail'),
    re_path(r'^profiles/(?P<pk>\d+)$', UserProfileDetail.as_view(),
        name='user-profile-detail'),
    re_path(r'^tokenlogin$', TokenLogin.as_view(), name='token-login'),
    re_path(r'^verification/$', UserVerification.as_view(),
        name='user-verification'),
    re_path(r'^export/$', UserDataExport.as_view(),
        name='user-export'),
    re_path(r'^password-strength$', PasswordStrengthDetail.as_view(),
        name='password-strength'),
    re_path(
        r'^(?P<pk>\d+)/avatar/(?P<size>\d+x\d+)$',
        AvatarImage.as_view(),
        name='avatar-image'
    ),
]
