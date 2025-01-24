from django.urls import re_path

from ..views import RedirectListView

urlpatterns = [
    re_path(r'^$', RedirectListView.as_view(), name='redirect-list')
]
