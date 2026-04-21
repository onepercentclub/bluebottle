import logging
from celery import shared_task
from django.db import connection
from rest_framework import generics, status, response, exceptions

from bluebottle.activity_pub.authentication import HTTPSignatureAuthentication
from bluebottle.activity_pub.models import (
    ActivityPubModel, Inbox
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.permissions import InboxPermission, ActivityPubPermission
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.serializers.base import ActivityPubSerializer
from bluebottle.clients.utils import LocalTenant


logger = logging.getLogger(__name__)


class JSONLDView(generics.RetrieveAPIView):
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]
    authentication_classes = [HTTPSignatureAuthentication]
    permission_classes = [ActivityPubPermission]
    serializer_class = ActivityPubSerializer
    queryset = ActivityPubModel.objects.filter(iri__isnull=True)

    def get_queryset(self):
        return self.queryset.filter(
            polymorphic_ctype__model=self.kwargs['type'].replace('-', '')
        )


@shared_task()
def create_task(request, tenant):
    with LocalTenant(tenant):
        try:
            serializer = ActivityPubSerializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except exceptions.ValidationError as e:
            print(e)
            logger.error(e)


class PickableRequest:
    pickled_fields = ['path', 'user', 'headers', 'auth', 'data']

    def __init__(self, request):
        for field in self.pickled_fields:
            setattr(self, field, getattr(request, field))


class InboxView(generics.CreateAPIView, JSONLDView):
    queryset = Inbox.objects.all()
    permission_classes = [InboxPermission]

    def get_serializer_context(self):
        return {'request': PickableRequest(self.request)}

    def create(self, request, *args, **kwargs):
        create_task.delay(PickableRequest(request), connection.tenant)
        return response.Response(status=status.HTTP_204_NO_CONTENT)
