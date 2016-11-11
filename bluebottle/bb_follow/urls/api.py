from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from ..views import FollowViewSet

router = DefaultRouter()
router.register(r'follows', FollowViewSet)

urlpatterns = [
    url(r'^', include(router.urls))
]
