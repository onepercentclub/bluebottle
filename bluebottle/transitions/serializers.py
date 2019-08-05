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
        user = self.context['request'].user
        transitions = value.transitions

        return (
            {
                'name': transition.name,
                'target': transition.target,
                'available': (
                    transition.is_possible(value.transitions) and
                    (user and transition.is_allowed(transitions, user))
                ),
                'conditions': {
                    condition.__name__: getattr(transitions, condition.__name__)()
                    for condition in transition.conditions if getattr(transitions, condition.__name__)()
                }
            }
            for transition in transitions.all_transitions
        )

    def get_attribute(self, instance):
        return instance


class TransitionSerializer(serializers.Serializer):
    transition = serializers.CharField()

    def save(self):
        resource = self.validated_data['resource']
        transition = self.validated_data['transition']

        available_transitions = resource.transitions.available_transitions(user=self.context['request'].user)

        if transition not in [available_transition.name for available_transition in available_transitions]:
            raise ValidationError('Transition is not available')

        self.instance = Transition(resource, transition)

        getattr(resource.transitions, transition)(send_messages=True, user=self.context['request'].user)
        resource.save()

    class Meta:
        fields = ('id', 'transition', 'resource')

    class JSONAPIMeta:
        resource_name = 'transitions'
