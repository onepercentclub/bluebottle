from builtins import object
from rest_framework import serializers

from bluebottle.members.serializers import UserPreviewSerializer
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()

    class Meta(object):
        model = ContactMessage
        fields = ('id', 'author', 'name', 'email', 'message', 'creation_date')
