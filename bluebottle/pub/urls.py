from django.urls import path
from . import views

app_name = 'pub'

urlpatterns = [
    path('actor', views.ActivityPubViewSet.as_view({'get': 'get_actor'}), name='actor'),
    path('outbox', views.ActivityPubViewSet.as_view({'get': 'get_outbox'}), name='outbox'),
]
