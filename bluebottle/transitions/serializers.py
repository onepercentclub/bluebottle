import uuid

from django.forms.models import model_to_dict

from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField


class Transition(object):
    def __init__(self, resource, transition):
        self.resource = resource
        self.transition = transition
        self.pk = str(uuid.uuid4())


class AvailableTransitionsField(ReadOnlyField):
    def to_representation(self, value):
        transitions = getattr(value, 'get_available_{}_transitions'.format(self.source))()

        return (
            {'name': transition['name'], 'target': transition['target']}
            for transition in transitions
            if 'form' not in transition or transition['form'](data=model_to_dict(value)).is_valid()
        )

    def get_attribute(self, instance):
        return instance


class TransitionSerializer(serializers.Serializer):
    transition = serializers.CharField()

    def save(self):
        resource = self.validated_data['resource']
        transition_name = self.validated_data['transition']

        transitions = getattr(resource, 'get_available_{}_transitions'.format(self.field))()

        if transition_name not in [transition['name'] for transition in transitions]:
            raise ValidationError('Transition is not available')

        self.instance = Transition(resource, transition_name)

        getattr(resource, transition_name)()
        resource.save()

    class Meta:
        fields = ('id', 'transition', 'resource')

    class JSONAPIMeta:
        resource_name = 'transitions'
