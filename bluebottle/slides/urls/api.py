from django.conf.urls import url

from ..views import SlideList

urlpatterns = [
    url(r'^$', SlideList.as_view(), name='slide_list'),
]
