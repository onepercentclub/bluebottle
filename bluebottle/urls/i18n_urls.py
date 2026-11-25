from django.urls import path
from django.urls import include, re_path
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import RedirectView

from bluebottle.views import HomeView
from bluebottle.utils.views import NoopView
from bluebottle.auth.views import admin_logout, TwoFactorSetupView, AdminLoginView
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

    re_path(
        '^admin/account/two_factor/setup/',
        TwoFactorSetupView.as_view(),
        name='setup',
    ),
    path('admin/account/login/', AdminLoginView.as_view(), name='admin-login'),
    path('admin/', include(tf_urls)),

    # Django JET URLS
    path('admin/jet/', include('jet.urls', 'jet')),
    path('admin/jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
    path('admin/locked/', locked_out, name='admin-locked-out'),

    re_path('admin/logout/', admin_logout),

    re_path(r'^admin/', admin.site.urls),

    path('admin/utils/tinymce/', include('tinymce.urls')),
    path('admin/utils/admintools/', include('admin_tools.urls')),

    # account login/logout, password reset, and password change
    path(
        'accounts/',
        include('django.contrib.auth.urls'),
    ),

    re_path(r'^admin', RedirectView.as_view(url=reverse_lazy('admin:index')), name='admin-slash'),
    re_path(r'^', HomeView.as_view(), name='home'),
]
