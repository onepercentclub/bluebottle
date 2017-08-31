from django.conf.urls import url

from bluebottle.homepage.views import HomePageDetail

urlpatterns = [
    url(r'^(?P<language>\w+)$', HomePageDetail.as_view(), name='homepage'),
]
