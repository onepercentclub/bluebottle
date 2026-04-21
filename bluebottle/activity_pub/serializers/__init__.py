from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer


from bluebottle.time_based.models import (
    DeadlineActivity, PeriodicActivity, RegisteredDateActivity, ScheduleActivity,
    DateActivity
)


class ActivityPubSerializer(PolymorphicSerializer):
    serializer_mapping = {}
    model_serializer_mapping = {}
    resource_type_field_name = 'type'

    def __init__(self, *args, full=True, include=False, **kwargs):
        super(PolymorphicSerializer, self).__init__(*args, **kwargs)

        self.resource_type_model_mapping = {}
        self.model_serializer_mapping = {}

        for model, serializer in self.serializer_mapping.items():
            resource_type = self.to_resource_type(model)
            if callable(serializer):
                serializer = serializer(
                    *args, full=full, include=include, **kwargs
                )
                serializer.parent = self

            self.resource_type_model_mapping[resource_type] = model
            self.model_serializer_mapping[model] = serializer

    def to_resource_type(self, model_or_instance):
        serializer = self.serializer_mapping[self._to_model(model_or_instance)]
        return serializer._declared_fields['type'].type

    def to_representation(self, instance):
        serializer = self._get_serializer_from_model_or_instance(instance)

        return serializer.to_representation(instance)

    @property
    def data(self):
        return super(serializers.Serializer, self).data


class FederatedObjectSerializer(PolymorphicSerializer):
    serializer_mapping = {}
    model_serializer_mapping = {}
    resource_type_field_name = 'type'

    def __init__(self, *args, **kwargs):
        super(PolymorphicSerializer, self).__init__(*args, **kwargs)

        self.resource_type_model_mapping = {}
        self.model_serializer_mapping = {}

        for model, serializer in self.serializer_mapping.items():
            resource_type = self.to_resource_type(model)
            if callable(serializer):
                serializer = serializer(*args, **kwargs)
                serializer.parent = self

            self.resource_type_model_mapping[resource_type] = model
            self.model_serializer_mapping[model] = serializer

        self.resource_type_model_mapping['ScheduleActivity'] = ScheduleActivity
        self.resource_type_model_mapping['PeriodicActivity'] = PeriodicActivity
        self.resource_type_model_mapping['RegisteredDateActivity'] = RegisteredDateActivity
        self.resource_type_model_mapping['DateActivity'] = DateActivity
        self.resource_type_model_mapping['DeadlineActivity'] = DeadlineActivity

    def _get_resource_type_from_mapping(self, mapping):
        resource_type = super()._get_resource_type_from_mapping(mapping)
        if resource_type == 'DoGoodEvent':
            if mapping.get('slot_mode', 'SetSlotMode') == 'ScheduledSlotMode':
                return 'ScheduleActivity'
            elif mapping.get('slot_mode', 'SetSlotMode') == 'PeriodicSlotMode':
                return 'PeriodicActivity'
            elif mapping.get('join_mode', None) in ('selected', 'SelectedJoinMode'):
                return 'RegisteredDateActivity'
            elif len(mapping.get('sub_event', [])) > 0:
                return 'DateActivity'
            else:
                return 'DeadlineActivity'

        return resource_type

    def to_resource_type(self, model_or_instance):
        serializer = self.serializer_mapping[self._to_model(model_or_instance)]
        return serializer._declared_fields['type'].type

    def to_representation(self, instance):
        serializer = self._get_serializer_from_model_or_instance(instance)
        return serializer.to_representation(instance)
