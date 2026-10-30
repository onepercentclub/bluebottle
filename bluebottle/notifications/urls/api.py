from django.urls import path

from bluebottle.notifications.views import (
    ActivityMessageDefaultList, ActivityMessageTemplateList, ActivityMessageTemplateDetail
)

urlpatterns = [
    path(
        '/message-defaults',
        ActivityMessageDefaultList.as_view(),
        name='activity-message-default-list'
    ),
    path(
        '/message-templates',
        ActivityMessageTemplateList.as_view(),
        name='activity-message-template-list'
    ),
    path(
        '/message-templates/<int:pk>',
        ActivityMessageTemplateDetail.as_view(),
        name='activity-message-template-detail'
    ),
]
