from django.conf.urls import url

from bluebottle.cms.views import ResultPageDetail

urlpatterns = [
    url(r'^results/(?P<pk>\d+)$', ResultPageDetail.as_view(), name='result-page-detail'),
]
