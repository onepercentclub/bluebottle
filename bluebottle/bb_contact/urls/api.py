from django.conf.urls import patterns, url

from ..views import ContactRequestCreate

urlpatterns = patterns('',
    url(r'^contact/$', ContactRequestCreate.as_view(), name='contact_request_create'),
)