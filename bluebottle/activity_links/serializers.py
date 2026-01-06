from django.db import models
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer

from bluebottle.activity_links.models import LinkedActivity, LinkedDeed, LinkedDateActivity, LinkedDeadlineActivity, \
    LinkedFunding
from bluebottle.utils.fields import RichTextField


class BaseLinkedActivitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title')
    summary = RichTextField(source='description')
    url = serializers.URLField(source='link')

    class Meta:
        model = LinkedActivity
        fields = ('name', 'summary', 'url')


class LinkedDeedSerializer(BaseLinkedActivitySerializer):
    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeed


class LinkedDateActivitySerializer(BaseLinkedActivitySerializer):
    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDateActivity


class LinkedDeadlineActivitySerializer(BaseLinkedActivitySerializer):
    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedDeadlineActivity


class LinkedFundingSerializer(BaseLinkedActivitySerializer):
    class Meta(BaseLinkedActivitySerializer.Meta):
        model = LinkedFunding
        fields = BaseLinkedActivitySerializer.Meta.fields + ('target', 'donated')


class LinkedActivitySerializer(PolymorphicSerializer):
    resource_type_field_name = 'type'

    polymorphic_serializers = [
        LinkedDeedSerializer,
        LinkedDateActivitySerializer,
        LinkedDeadlineActivitySerializer,
        LinkedFundingSerializer
    ]

    model_type_mapping = {
        LinkedDeed: 'GoodDeed',
        LinkedDateActivity: 'DoGoodEvent',
        LinkedDeadlineActivity: 'DoGoodEvent',
        LinkedFunding: 'Funding',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Map resource types to models for polymorphic deserialization
        self.resource_type_model_mapping['DateActivity'] = LinkedDateActivity
        self.resource_type_model_mapping['DeadlineActivity'] = LinkedDeadlineActivity
        self.resource_type_model_mapping['Funding'] = LinkedFunding
        self.resource_type_model_mapping['GoodDeed'] = LinkedDeed

    def _get_resource_type_from_mapping(self, data):
        event_type = data.get('type')

        # Map CrowdFunding to Funding for LinkedFunding
        if event_type == 'CrowdFunding':
            return 'Funding'

        # Handle DoGoodEvent - check sub_event to distinguish DateActivity from DeadlineActivity
        if event_type == 'DoGoodEvent':
            if len(data.get('sub_event', [])) > 0:
                return 'DateActivity'
            else:
                return 'DeadlineActivity'

        # For GoodDeed, return as-is
        if event_type == 'GoodDeed':
            return 'GoodDeed'

        return super()._get_resource_type_from_mapping(data)

    def to_resource_type(self, model_or_instance):
        if isinstance(model_or_instance, models.Model):
            model = type(model_or_instance)
        else:
            model = model_or_instance
        return self.model_type_mapping[model]

    model_serializer_mapping = {
        LinkedDeed: LinkedDeedSerializer,
        LinkedDateActivity: LinkedDateActivitySerializer,
        LinkedDeadlineActivity: LinkedDeadlineActivitySerializer,
        LinkedFunding: LinkedFundingSerializer
    }

    class Meta:
        model = LinkedActivity
