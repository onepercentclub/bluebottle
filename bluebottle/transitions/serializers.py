from builtins import str
from builtins import object
import uuid

from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField


class Transition(object):
    def __init__(self, resource, transition, message=None):
        self.resource = resource
        self.message = message
        self.transition = transition
        self.pk = str(uuid.uuid4())


class AvailableTransitionsField(ReadOnlyField):
    def to_representation(self, value):
        user = self.context['request'].user
        transitions = getattr(value, self.source)

        return tuple(
            {
                'name': transition.name,
                'target': transition.target.value,
                'available': True,
            }
            for transition in transitions.possible_transitions(user=user)
            if not transition.options.get('automatic')
        )

    def get_attribute(self, instance):
        return instance


class TransitionSerializer(serializers.Serializer):
    transition = serializers.CharField()
    message = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    field = 'states'

    def save(self):
        resource = self.validated_data['resource']
        transition = self.validated_data['transition']
        message = self.validated_data.get('message', '')

        available_transitions = getattr(resource, self.field).available_transitions(user=self.context['request'].user)

        if transition not in [available_transition.name for available_transition in available_transitions]:
            raise ValidationError('Transition is not available')

        self.instance = Transition(resource, transition)

        getattr(getattr(resource, self.field), transition)(
            message=message,
            send_messages=True,
            user=self.context['request'].user)
        resource.save()

    class Meta(object):
        fields = ('id', 'transition', 'message', 'resource')

    class JSONAPIMeta(object):
        resource_name = 'transitions'
