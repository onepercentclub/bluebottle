from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bluebottle.clients import properties
from bluebottle.payouts_dorado.models import Payout
from bluebottle.payouts_dorado.permissions import IsFinancialMember
from bluebottle.payouts_dorado.serializers import PayoutSerializer, ProjectPayoutSerializer
from bluebottle.projects.models import Project


class ProjectPayoutDetail(generics.RetrieveAPIView):
    queryset = Project.objects.filter(campaign_ended__isnull=False).all()
    serializer_class = ProjectPayoutSerializer
    permission_classes = (IsFinancialMember,)


class PayoutDetail(generics.UpdateAPIView):
    permission_classes = (IsFinancialMember,)
    serializer_class = PayoutSerializer

    def get_object(self):
        data = self.request.data
        remote_id = data['id']
        project_id = data['project_id']
        obj, created = Payout.objects.get_or_create(remote_id=remote_id, project_id=project_id)
        return obj


class PaymentMethodList(APIView):
    permission_classes = (IsFinancialMember,)

    def get(self, request, *args, **kwargs):
        methods = getattr(properties, 'PAYOUT_METHODS', ())
        return Response(methods, status=status.HTTP_200_OK)
