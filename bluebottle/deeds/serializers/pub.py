from rest_framework import serializers
from django.urls import reverse


class DeedJSONLDSerializer(serializers.Serializer):
    """JSON-LD Serializer for Deed model"""

    @property
    def context(self):
        return {
            "@context": {
                "title": "http://schema.org/name",
                "description": "http://schema.org/description",
                "status": "http://schema.org/status",
                "start": "http://schema.org/startDate",
                "end": "http://schema.org/endDate",
                "permissions": "http://schema.org/permit",
                "contributors": "http://schema.org/contributor",
            }
        }

    @property
    def id(self):
        return reverse("deed-detail", args=[self.instance.pk]) if self.instance else None

    @property
    def type(self):
        return "Deed"

    title = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField()
    start = serializers.DateField(allow_null=True)
    end = serializers.DateField(allow_null=True)
    permissions = serializers.CharField(source="get_permissions", read_only=True)
    contributors = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source="participants")

    def to_representation(self, instance):
        """Convert to JSON-LD format"""
        data = super().to_representation(instance)
        return {
            "@context": self.context,
            "@id": self.id,
            "@type": self.type,
            **data
        }
