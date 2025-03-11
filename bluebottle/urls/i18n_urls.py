from django.urls import include, re_path
from django.contrib import admin
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.views.generic import RedirectView

from bluebottle.views import HomeView
from bluebottle.utils.views import NoopView
from bluebottle.auth.views import admin_password_reset, admin_logout
from bluebottle.auth.utils import AdminSiteOTPRequired
from bluebottle.bluebottle_dashboard.views import locked_out
from bluebottle.looker.dashboard_views import LookerEmbedView # noqa This has to be imported early so that custom urls will work
from bluebottle.analytics.views import PlausibleEmbedView # noqa This has to be imported early so that custom urls will work

from two_factor.urls import urlpatterns as tf_urls


admin.site.__class__ = AdminSiteOTPRequired
admin.autodiscover()


urlpatterns = [
    re_path(
        '^admin/account/two_factor/disable/',
        NoopView.as_view(),
    ),
    re_path(
        '^admin/account/two_factor/backup/tokens/',
        NoopView.as_view(),
    ),
    re_path(r'^admin/two_factor/', include(tf_urls)),

    # Django JET URLS
    re_path(r'^admin/jet/', include('jet.urls', 'jet')),
    re_path(r'^admin/jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
    re_path(r'^admin/locked/$', locked_out, name='admin-locked-out'),

    re_path('admin/logout/', admin_logout),

    # Django Admin, docs and password reset
    re_path(
        r'^admin/password_reset/$',
        admin_password_reset,
        name='admin_password_reset'
    ),
    re_path(
        r'^admin/password_reset/done/$',
        PasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    re_path(
        r'^admin/password_reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    re_path(
        r'^admin/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(),
        {'post_reset_redirect': '/admin'}, name='password_reset_confirm'
    ),
    re_path(r'^admin/', admin.site.urls),

    re_path(r'^admin/utils/tinymce/', include('tinymce.urls')),
    re_path(r'^admin/utils/admintools/', include('admin_tools.urls')),

    # account login/logout, password reset, and password change
    re_path(
        r'^accounts/',
        include('django.contrib.auth.urls'),
    ),

    re_path(r'^admin', RedirectView.as_view(url=reverse_lazy('admin:index')), name='admin-slash'),
    re_path(r'^', HomeView.as_view(), name='home'),
]
