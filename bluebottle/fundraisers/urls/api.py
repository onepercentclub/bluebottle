from django.conf.urls import url

from bluebottle.fundraisers.views import FundraiserListView, FundraiserDetailView

urlpatterns = [
    url(r'^$', FundraiserListView.as_view(),
        name='fundraiser-list'),
    url(r'(?P<pk>[\d]+)$', FundraiserDetailView.as_view(),
        name='fundraiser-detail'),
]
