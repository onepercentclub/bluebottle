from django.conf.urls import url

from bluebottle.redirects.views import RedirectListView

urlpatterns = [
    url(r'^$', RedirectListView.as_view(), name='redirect-list')
]
