from django.conf.urls import patterns, url

from ..views import CategoryList

urlpatterns = patterns(
    '',
    url(r'^$', CategoryList.as_view(), name='category-list'),
)
