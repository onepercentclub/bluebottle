from django.db import connection
from django.urls import reverse

from rest_framework import serializers

from bluebottle.activity_pub.models import Inbox, Outbox, PublicKey
from bluebottle.activity_pub.serializers.base import (
    FederatedObjectSerializer
)
from bluebottle.geo.models import Geolocation
from bluebottle.organizations.models import Organization
from bluebottle.time_based.models import DeadlineActivity, DateActivity
from bluebottle.deeds.models import Deed
from bluebottle.files.models import Image
from bluebottle.collect.models import CollectActivity, CollectType
from bluebottle.funding.models import Funding
from bluebottle.utils.fields import MoneyField

from bluebottle.utils.fields import RichTextField
from bluebottle.files.serializers import ImageField


class RelatedFederatedObjectField(serializers.Field):
    def __init__(self, serializer, *args, **kwargs):
        self.serializer = serializer

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        pass

    def to_internal_value(self, data):
        pass


class FederatedActivitySerializer(FederatedObjectSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description')

    image = ImageField()

    class Meta:
        fields = FederatedObjectSerializer.Meta.fields + ('name', 'summary', 'image')


class CollectTypeSerializer(FederatedObjectSerializer):
    name = serializers.CharField()

    class Meta:
        model = CollectType


class LocationSerializer(FederatedObjectSerializer):
    class Meta:
        model = Geolocation


class IdField(serializers.CharField):
    def __init__(self, url_name):
        self.url_name = url_name
        super().__init__(source='*')

    def to_representation(self, value):
        return value.activity_pub_url


class ImageSerializer(FederatedObjectSerializer):
    id = IdField('json-ld:image')
    url = serializers.SerializerMethodField()
    name = serializers.CharField()

    def get_url(self, instance):
        return connection.tenant.build_absolute_url(
            reverse('activity-image', args=(instance.activity_set.first().pk, '1568x882'))

        )

    class Meta:
        model = Image
        fields = FederatedObjectSerializer.Meta.fields + (
            'url', 'name'
        )


class FederatedDeedSerializer(FederatedActivitySerializer):
    id = IdField('json-ld:good-deed')
    startTime = serializers.DateField(source='start')
    endTime = serializers.DateField(source='end')
    image = ImageSerializer()

    class Meta:
        model = Deed
        fields = FederatedActivitySerializer.Meta.fields + (
            'startTime', 'endTime'
        )


class FederatedCollectSerializer(FederatedActivitySerializer):
    location = RelatedFederatedObjectField(LocationSerializer)

    start = serializers.DateField()
    end = serializers.DateField()

    collect_type = RelatedFederatedObjectField(CollectTypeSerializer)

    target = serializers.DecimalField(decimal_places=2, max_digits=10)
    realized = serializers.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        model = CollectActivity


class FederatedFundingSerializer(FederatedActivitySerializer):
    location = RelatedFederatedObjectField(LocationSerializer)

    start = serializers.DateField()
    end = serializers.DateField()

    target = MoneyField()
    realized = MoneyField()

    class Meta:
        model = Funding


class FederatedDeadlineActivitySerializer(FederatedActivitySerializer):
    location = RelatedFederatedObjectField(LocationSerializer)

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


class FederatedOrganizationSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    summary = serializers.CharField(source="description", allow_blank=True)
    icon = serializers.SerializerMethodField(required=False)
    preferred_username = serializers.CharField(source="slug")

    def get_icon(self, obj):
        logo = connection.tenant.build_absolute_url(obj.logo.url) if obj.logo else None
        return logo

    class Meta:
        model = Organization
        fields = ('name', 'summary', 'icon', 'preferred_username')
