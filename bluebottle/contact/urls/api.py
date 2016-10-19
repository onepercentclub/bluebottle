from django.conf.urls import url

from ..views import ContactRequestCreate

urlpatterns = [
    url(r'^$', ContactRequestCreate.as_view(),
        name='contact_request_create'),
]
