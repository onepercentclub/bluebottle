from datetime import timedelta

from django.utils.timezone import now
from rest_framework import serializers
from rest_framework_json_api.serializers import Serializer
from django.utils.translation import gettext_lazy as _


class SocialLoginSerializer(Serializer):
    code = serializers.CharField(write_only=True, required=False)
    access_token = serializers.CharField(write_only=True, required=False)
    signed_request = serializers.CharField(write_only=True, required=False)
    token = serializers.CharField(read_only=True)
    backend = serializers.CharField(write_only=True)

    class Meta:
        fields = ['code', 'signed_request', 'token', 'backend']

    class JSONAPIMeta:
        resource_name = 'social/tokens'
