from rest_framework import serializers

from bluebottle.utils.serializer_dispatcher import get_serializer_class

from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    author = get_serializer_class('AUTH_USER_MODEL', 'preview')()

    class Meta:
        model = ContactMessage
        fields = ('id', 'author', 'name', 'email', 'message', 'creation_date')
