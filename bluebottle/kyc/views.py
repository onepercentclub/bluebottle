from rest_framework import generics

from bluebottle.kyc.models import AccountVerification
from bluebottle.kyc.serializers import VerificationSerializer


class VerificationCreateView(generics.CreateAPIView):

    serializer_class = VerificationSerializer
    model = AccountVerification
