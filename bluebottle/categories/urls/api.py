from django.conf.urls import url

from ..views import CategoryList, CategoryDetail

urlpatterns = [
    url(r'^$', CategoryList.as_view(), name='category-list'),
    url(r'^(?P<pk>\d+)$', CategoryDetail.as_view(), name='category-detail'),
]
