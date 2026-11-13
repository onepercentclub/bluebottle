from django.urls import path

from bluebottle.cta.views import ActionDetail, ActionList

urlpatterns = [
    path('/actions', ActionList.as_view(), name='cta-action-list'),
    path('/actions/<str:pk>', ActionDetail.as_view(), name='cta-action-detail'),
]
