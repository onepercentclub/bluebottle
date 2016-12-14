from django.conf.urls import url

from ..views import RedirectListView

urlpatterns = [
    url(r'^$', RedirectListView.as_view(), name='redirect-list')
]
