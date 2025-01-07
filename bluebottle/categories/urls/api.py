from django.urls import re_path

from ..views import CategoryList, CategoryDetail

urlpatterns = [
    re_path(r'^$', CategoryList.as_view(), name='category-list'),
    re_path(r'^(?P<pk>\d+)$', CategoryDetail.as_view(), name='category-detail'),
]
