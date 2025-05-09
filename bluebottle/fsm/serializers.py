import uuid
from builtins import object
from builtins import str

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField

from bluebottle.fsm.state import TransitionNotPossible
from rest_framework_json_api.serializers import Serializer


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

        transtisions = (
            {
                "name": transition.field,
                "target": transition.target.value,
                "label": transition.name,
                "passed_label": transition.passed_label,
                "description": transition.description_front_end,
                "short_description": transition.short_description,
                "available": True,
            }
            for transition in states.possible_transitions(user=user)
            if not transition.automatic
        )

        preferred_order = [
            "approve", "request_changes",
            "reopen", "reopen_manually",
            "succeed_manually", "succeed",
            "submit", "restore",
            "cancel", "reject", "delete"
        ]

        sorted_transitions = sorted(
            transtisions,
            key=lambda x: preferred_order.index(x["name"]) if x["name"] in preferred_order else len(preferred_order))
        return sorted_transitions

    def get_attribute(self, instance):
        return instance


class CurrentStatusField(ReadOnlyField):
    def to_representation(self, value):
        return {
            'value': value.value,
            'name': value.name.title(),
            'description': value.description,
        }


class TransitionSerializer(Serializer):
    transition = serializers.CharField()
    message = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    send_email = serializers.BooleanField(default=True, allow_null=True)

    field = 'states'

    def save(self):
        resource = self.validated_data["resource"]
        transition_name = self.validated_data["transition"]
        message = self.validated_data.get("message", None)
        send_email = self.validated_data.get("send_email", True)
        if send_email is None:
            send_email = True
        states = getattr(resource, self.field)
        user = self.context['request'].user

        try:
            transition = states.transitions[transition_name]
            transition.can_execute(states, user=user, automatic=False)
        except (TransitionNotPossible, KeyError):
            raise ValidationError('Transition is not available')

        self.instance = Transition(resource, transition_name, message)

        transition.execute(states)
        resource.execute_triggers(user=user, send_messages=send_email, message=message)
        resource.save()

    class Meta(object):
        fields = ('id', 'transition', 'message', 'resource')

    class JSONAPIMeta(object):
        resource_name = 'transitions'
