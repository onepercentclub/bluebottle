from builtins import object
from rest_framework import serializers

from .models import Redirect


class RedirectSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Redirect
        fields = ('id', 'old_path', 'new_path', 'fallback_redirect')
