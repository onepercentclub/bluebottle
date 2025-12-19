from django.db import models
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_links.models import LinkedActivity, LinkedDeed, LinkedDateActivity, LinkedDeadlineActivity
from bluebottle.utils.fields import RichTextField


class BaseLinkedActivitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description')
    url = serializers.URLField(source='link')

    class Meta:
        model = LinkedActivity
        fields = ('name', 'summary', 'url')


class LinkedDeedSerializer(BaseLinkedActivitySerializer):
    class Meta:
        model = LinkedDeed
        fields = BaseLinkedActivitySerializer.Meta.fields


class LinkedDateActivitySerializer(BaseLinkedActivitySerializer):
    class Meta:
        model = LinkedDateActivity


class LinkedDeadlineActivitySerializer(BaseLinkedActivitySerializer):
    class Meta:
        model = LinkedDeadlineActivity


class LinkedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    polymorphic_serializers = [
        LinkedDeedSerializer,
        LinkedDateActivitySerializer,
        LinkedDeadlineActivitySerializer,
    ]

    model_type_mapping = {
        LinkedDeed: 'GoodDeed',
        LinkedDateActivity: 'DoGoodEvent',
        LinkedDeadlineActivity: 'DoGoodEvent',
    }

    def _get_resource_type_from_mapping(self, data):
        if data.get('type') == 'DoGoodEvent':
            if len(data.get('sub_event', [])) > 0:
                return 'DateActivity'
            else:
                return 'DeadlineActivity'
        return super()._get_resource_type_from_mapping(data)

    def to_resource_type(self, model_or_instance):
        if isinstance(model_or_instance, models.Model):
            model = type(model_or_instance)
        else:
            model = model_or_instance
        return self.model_type_mapping[model]

    model_serializer_mapping = {
        LinkedDeed: 'LinkedDeedSerializer',
        LinkedDateActivity: 'LinkedDateActivitySerializer',
        LinkedDeadlineActivity: 'LinkedDeadlineActivitySerializer',
    }

    class Meta:
        model = LinkedActivity
