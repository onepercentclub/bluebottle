from django.conf.urls import url
from ..views import ai

urlpatterns = [
    url(r'^$', ai, name='ai'),
]
