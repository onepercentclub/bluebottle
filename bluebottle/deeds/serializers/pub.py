from rest_framework import serializers
from django.urls import reverse
from bluebottle.deeds.models import Deed


class DeedJSONLDSerializer(serializers.Serializer):
    """JSON-LD Serializer for Deed model with ActivityPub support"""

    @property
    def context(self):
        return {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                {
                    "title": "http://schema.org/name",
                    "description": "http://schema.org/description",
                    "status": "http://schema.org/status",
                    "start": "http://schema.org/startDate",
                    "end": "http://schema.org/endDate",
                    "permissions": "http://schema.org/permit",
                    "contributors": "http://schema.org/contributor",
                }
            ]
        }

    @property
    def id(self):
        return reverse("deed-detail", args=[self.instance.pk]) if self.instance else None

    @property
    def type(self):
        return "Deed"

    title = serializers.CharField()
    description = serializers.SerializerMethodField()
    status = serializers.CharField()
    start = serializers.DateField(allow_null=True)
    end = serializers.DateField(allow_null=True)
    permissions = serializers.CharField(source="get_permissions", read_only=True)
    contributors = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source="participants")

    def to_representation(self, instance):
        """Convert to ActivityPub and JSON-LD format"""
        data = super().to_representation(instance)
        activity_pub_data = {
            "@context": self.context,
            "@id": self.id,
            "@type": "Create",
            "actor": f"{self.context['request'].build_absolute_uri('/')}actor",
            "object": {
                "@type": self.type,
                "name": data['title'],
                "content": data['description'],
                "published": instance.created.isoformat(),
                "startTime": data['start'],
                "endTime": data['end'],
                **data
            }
        }
        return activity_pub_data

    def get_description(self, obj):
        # Return the HTML description
        return obj.description_html


class DeedActivityPubSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    name = serializers.CharField(source='title')
    content = serializers.CharField(source='description.html')
    startTime = serializers.DateField(source='start')
    endTime = serializers.DateField(source='end')
    published = serializers.DateTimeField(source='created')
    updated = serializers.DateTimeField(source='updated')
    maximumAttendeeCapacity = serializers.IntegerField(source='target', required=False)
    location = serializers.SerializerMethodField()

    class Meta:
        model = Deed
        fields = (
            'type', 'id', 'name', 'content',
            'startTime', 'endTime', 'published', 'updated',
            'maximumAttendeeCapacity', 'location'
        )

    def get_type(self, obj):
        return "Event"

    def get_id(self, obj):
        request = self.context.get('request')
        return f"{request.scheme}://{request.get_host()}/ap/deeds/{obj.pk}"

    def get_location(self, obj):
        request = self.context.get('request')
        return f"{request.scheme}://{request.get_host()}"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add ActivityPub context
        data['@context'] = [
            "https://www.w3.org/ns/activitystreams",
            {
                "Deed": "https://schema.org/Event",
                "startTime": "https://schema.org/startDate",
                "endTime": "https://schema.org/endDate"
            }
        ]

        # Remove null values
        return {k: v for k, v in data.items() if v is not None}
