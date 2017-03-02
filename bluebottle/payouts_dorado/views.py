from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bluebottle.clients import properties
from bluebottle.payouts_dorado.permissions import IsFinancialMember
from bluebottle.projects.models import Project
from bluebottle.payouts_dorado.serializers import ProjectPayoutSerializer


class ProjectPayoutDetail(generics.RetrieveUpdateAPIView):
    queryset = Project.objects.filter(campaign_ended__isnull=False).all()
    serializer_class = ProjectPayoutSerializer
    permission_classes = (IsFinancialMember,)


class PayoutMethodList(APIView):
    permission_classes = (IsFinancialMember,)

    def get(self, request, *args, **kwargs):
        methods = getattr(properties, 'PAYOUT_METHODS', ())
        return Response(methods, status=status.HTTP_200_OK)
