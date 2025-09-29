from io import BytesIO

import requests

from django.core.files import File
from django.db import connection, models
from django.urls import reverse

from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_pub.models import Image as ActivityPubImage
from bluebottle.activity_pub.serializers.base import (
    FederatedObjectSerializer
)
from bluebottle.geo.models import Geolocation
from bluebottle.time_based.models import DeadlineActivity, DateActivity
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image
from bluebottle.collect.models import CollectActivity, CollectType
from bluebottle.funding.models import Funding
from bluebottle.utils.fields import MoneyField

from bluebottle.utils.fields import RichTextField


class IdField(serializers.CharField):
    def __init__(self, url_name):
        self.url_name = url_name
        super().__init__(source='*')

    def to_representation(self, value):
        return value.activity_pub_url

    def to_internal_value(self, value):
        return {'id': value}


class ImageSerializer(FederatedObjectSerializer):
    id = IdField('json-ld:image')
    url = serializers.SerializerMethodField()
    name = serializers.CharField()

    def get_url(self, instance):
        return connection.tenant.build_absolute_url(
            reverse('activity-image', args=(instance.activity_set.first().pk, '1568x882'))

        )

    def create(self, validated_data):
        image = ActivityPubImage.objects.get(iri=validated_data['id'])
        response = requests.get(image.url, timeout=30)
        response.raise_for_status()

        validated_data['file'] = File(BytesIO(response.content), name=validated_data['name'])

        return super().create(validated_data)

    def save(self, *args, **kwargs):
        return super().save(owner=self.context['request'].user)

    class Meta:
        model = Image
        fields = FederatedObjectSerializer.Meta.fields + (
            'url', 'name'
        )


class FederatedActivitySerializer(FederatedObjectSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description')

    class Meta:
        fields = FederatedObjectSerializer.Meta.fields + ('name', 'summary', 'image')


class CollectTypeSerializer(FederatedActivitySerializer):
    name = serializers.CharField()

    class Meta:
        model = CollectType


class LocationSerializer(FederatedObjectSerializer):
    class Meta:
        model = Geolocation


class FederatedDeedSerializer(FederatedActivitySerializer):
    id = IdField('json-ld:good-deed')
    startTime = serializers.DateField(source='start', allow_null=True)
    endTime = serializers.DateField(source='end', allow_null=True)
    image = ImageSerializer()

    class Meta:
        model = Deed
        fields = FederatedActivitySerializer.Meta.fields + (
            'startTime', 'endTime'
        )


class FederatedCollectSerializer(FederatedActivitySerializer):
    location = LocationSerializer()

    start = serializers.DateField()
    end = serializers.DateField()

    collect_type = CollectTypeSerializer()

    target = serializers.DecimalField(decimal_places=2, max_digits=10)
    realized = serializers.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        model = CollectActivity


class FederatedFundingSerializer(FederatedActivitySerializer):
    location = LocationSerializer()

    start = serializers.DateField()
    end = serializers.DateField()

    target = MoneyField()
    realized = MoneyField()

    class Meta:
        model = Funding


class FederatedDeadlineActivitySerializer(FederatedActivitySerializer):
    location = LocationSerializer()

    start = serializers.DateField()
    end = serializers.DateField()

    class Meta:
        model = DeadlineActivity


class FederatedDateActivitySerializer(FederatedActivitySerializer):
    start = serializers.DateField()
    end = serializers.DateField()

    #  slots = RelatedFederatedObjectField(SlotSerializer)

    class Meta:
        model = DateActivity


class FederatedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    model_serializer_mapping = {
        DeadlineActivity: FederatedDeadlineActivitySerializer,
        Deed: FederatedDeedSerializer,
        CollectActivity: FederatedCollectSerializer,
        DateActivity: FederatedDateActivitySerializer,
        DeadlineActivity: FederatedDeadlineActivitySerializer,
        Funding: FederatedFundingSerializer
    }

    model_type_mapping = {
        Deed: 'GoodDeed',
        Funding: 'CrowdFunding',
        CollectActivity: 'CollectionDrive'
    }

    def to_resource_type(self, model_or_instance):
        if isinstance(model_or_instance, models.Model):
            model = type(model_or_instance)
        else:
            model = model_or_instance

        return self.model_type_mapping.get(model, 'unknown')

    def save(self, *args, **kwargs):
        return super().save(owner=self.context['request'].user)
