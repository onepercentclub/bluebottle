from django.urls import path

from bluebottle.redirects.views import RedirectListView

urlpatterns = [
    path('', RedirectListView.as_view(), name='redirect-list')
]
