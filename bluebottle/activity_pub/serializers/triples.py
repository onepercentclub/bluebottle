from rest_framework import serializers, exceptions
from rest_framework.reverse import reverse

from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.members.models import Member

from bluebottle.activity_pub.resources import Resource
from bluebottle.activity_pub.processor import (
    processed_context, processor, default_context
)

from django.db import connection


class JSONLDSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.include = kwargs.pop('include', [])

        super().__init__(*args, **kwargs)

    class Meta:
        pass

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['@type'] = self.Meta.type
        representation['@id'] = connection.tenant.build_absolute_url(
            reverse(self.Meta.url_name, args=(value.pk, ))
        )
        representation['@context'] = default_context
        return representation


class TypeField(serializers.Field):
    def __init__(self, iri):
        self.iri = processor._expand_iri(processed_context, 'type', None, True)
        self.value = processor._expand_iri(processed_context, iri, None, True)
        super().__init__(read_only=True)

    def to_representation(self, value):
        return self.value


class ImageField(serializers.Field):
    def to_representation(self, value):
        try:
            return {
                '@type': 'Image',
                '@id': connection.tenant.build_absolute_url(
                    reverse('activity_pub:resource', args=('Image', f'organization-{value.instance.pk}', ))
                ),
                '@context': default_context,
                'url': connection.tenant.build_absolute_url(
                    value.url
                )
            }
        except ValueError:
            return None


class OrganizationSerializer(JSONLDSerializer):
    name = serializers.CharField()
    summary = serializers.CharField(source='description')
    icon = ImageField(source='logo')

    class Meta:
        type = 'Organization'
        model = Member
        url_name = 'activity_pub:organization'
        fields = ('name', 'summary', 'icon')
