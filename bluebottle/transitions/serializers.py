import uuid

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

        return dict((transition.name, {'target': transition.target}) for transition in transitions)

    def get_attribute(self, instance):
        return instance


class TransitionSerializer(serializers.Serializer):
    transition = serializers.CharField()

    def save(self):
        resource = self.validated_data['resource']
        transition = self.validated_data['transition']

        available_transitions = getattr(resource, 'get_available_{}_transitions'.format(self.field))()
        if transition not in [available_transition.name for available_transition in available_transitions]:
            raise ValidationError('Transition is not available')

        self.instance = Transition(resource, transition)

        getattr(resource, transition)()
        resource.save()

    class Meta:
        fields = ('id', 'transition', )

    class JSONAPIMeta:
        resource_name = 'transitions'
