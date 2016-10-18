from django.conf.urls import url

from ..views import CategoryList

urlpatterns = [
    url(r'^$', CategoryList.as_view(), name='category-list'),
]
