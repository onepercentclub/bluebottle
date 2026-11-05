
from django.urls import path
from django.urls import re_path
from bluebottle.bb_accounts.views import (
    UserActivityDetail, CurrentMemberDetail,
    PasswordReset, PasswordResetConfirm, UserDataExport, EmailSetView,
    PasswordSetView, Logout, MemberDetail, SignUpToken,
    SignUpTokenConfirmation, CaptchaVerification,
    PasswordStrengthDetail, MemberSignUp,
    MemberProfileDetail, AvatarImage, AuthenticationMethodList
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
    path('signup-token', SignUpToken.as_view(), name='user-signup-token'),
    path('signup-token/confirm', SignUpTokenConfirmation.as_view(), name='user-signup-token-confirm'),
    path('captcha', CaptchaVerification.as_view(), name='captcha-verification'),
    path('user-activities/', UserActivityDetail.as_view(), name='user-activity'),
    path('email', EmailSetView.as_view(), name='user-set-email'),
    path('password', PasswordSetView.as_view(), name='user-set-password'),
    path('logout', Logout.as_view(), name='user-logout'),
    path('passwordreset', PasswordReset.as_view(), name='password-reset'),
    path('passwordreset/confirm', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
    re_path(r'^members/?$', MemberSignUp.as_view(), name='member-signup'),
    path('member/current', CurrentMemberDetail.as_view(), name='current-member-detail'),
    path('member/profile/<int:pk>', MemberProfileDetail.as_view(), name='member-profile-detail'),
    path('member/<int:pk>', MemberDetail.as_view(), name='member-detail'),
    path(
        'authentication-methods', AuthenticationMethodList.as_view(),
        name='authentication-method-list'
    ),
    path(
        'export/', UserDataExport.as_view(),
        name='user-export'
    ),
    path(
        'password-strength', PasswordStrengthDetail.as_view(),
        name='password-strength'
    ),
    re_path(
        r'^(?P<pk>\d+)/avatar/(?P<size>\d+(x\d+)?)$',
        AvatarImage.as_view(),
        name='avatar-image'
    ),
]
