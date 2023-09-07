import uuid
from builtins import object
from builtins import str

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField

from bluebottle.fsm.state import TransitionNotPossible


class Transition(object):
    def __init__(self, resource, transition, message=None):
        self.resource = resource
        self.message = message
        self.transition = transition
        self.pk = str(uuid.uuid4())


class AvailableTransitionsField(ReadOnlyField):
    def to_representation(self, value):
        user = self.context['request'].user
        states = getattr(value, self.source)

        return (
            {
                'name': transition.field,
                'target': transition.target.value,
                'label': transition.target.name,
                'description': transition.target.description,
                'available': True,
            }
            for transition in states.possible_transitions(user=user)
            if not transition.automatic
        )

    def get_attribute(self, instance):
        return instance


class TransitionSerializer(serializers.Serializer):
    transition = serializers.CharField()
    message = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    field = 'states'

    def save(self):
        resource = self.validated_data['resource']
        transition_name = self.validated_data['transition']
        message = self.validated_data.get('message', '')
        states = getattr(resource, self.field)
        user = self.context['request'].user

        try:
            transition = states.transitions[transition_name]
            transition.can_execute(states, user=user, automatic=False)
        except (TransitionNotPossible, KeyError):
            raise ValidationError('Transition is not available')

        self.instance = Transition(resource, transition_name, message)

        transition.execute(states)
        resource.execute_triggers(user=user, send_messages=True, message=message)
        resource.save()

    class Meta(object):
        fields = ('id', 'transition', 'message', 'resource')

    class JSONAPIMeta(object):
        resource_name = 'transitions'
