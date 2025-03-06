from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

from bluebottle.deeds.views import DeedViewSet

router = DefaultRouter()
router.register(r'pub', DeedViewSet, basename='deed')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    re_path('/', include(router.urls)),
]
