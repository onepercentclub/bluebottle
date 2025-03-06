from rest_framework import serializers
from .models import Platform


class PlatformActivityPubSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    preferredUsername = serializers.CharField(source='name')
    inbox = serializers.URLField(source='inbox_url')
    outbox = serializers.URLField(source='outbox_url')
    publicKey = serializers.SerializerMethodField()

    class Meta:
        model = Platform
        fields = (
            'type', 'id', 'preferredUsername',
            'inbox', 'outbox', 'publicKey'
        )

    def get_type(self, obj):
        return "Application"

    def get_id(self, obj):
        return obj.actor_url

    def get_publicKey(self, obj):
        return {
            "id": f"{obj.actor_url}#main-key",
            "owner": obj.actor_url,
            "publicKeyPem": obj.public_key
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['@context'] = "https://www.w3.org/ns/activitystreams"
        return data
