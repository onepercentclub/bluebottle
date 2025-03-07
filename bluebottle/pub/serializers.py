from rest_framework import serializers

from bluebottle.deeds.models import Deed
from bluebottle.pub.models import RemoteDeed

from .models import ActivityPubRegistration, Platform


class PlatformActivityPubSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    preferredUsername = serializers.CharField(source="name")
    inbox = serializers.URLField(source="inbox_url")
    outbox = serializers.URLField(source="outbox_url")
    publicKey = serializers.SerializerMethodField()

    class Meta:
        model = Platform
        fields = ("type", "id", "preferredUsername", "inbox", "outbox", "publicKey")

    def get_type(self, obj):
        return "Application"

    def get_id(self, obj):
        return obj.actor_url

    def get_publicKey(self, obj):
        return {
            "id": f"{obj.actor_url}#main-key",
            "owner": obj.actor_url,
            "publicKeyPem": obj.public_key,
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["@context"] = "https://www.w3.org/ns/activitystreams"
        return data


class DeedSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    eventStatus = serializers.SerializerMethodField()
    organizer = serializers.SerializerMethodField()

    class Meta:
        model = Deed
        fields = (
            "type",
            "name",
            "description",
            "startDate",
            "endDate",
            "eventStatus",
            "maximumAttendeeCapacity",
            "organizer",
        )

    def get_type(self, obj):
        return "Event"

    def get_eventStatus(self, obj):
        return "https://schema.org/EventScheduled"

    def get_organizer(self, obj):
        return {
            "type": "Person",
            "name": obj.owner.get_full_name() or obj.owner.username,
        }


class ActivityPubRegistrationSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    agent = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    actionStatus = serializers.CharField(source="status")

    class Meta:
        model = ActivityPubRegistration
        fields = ("type", "agent", "object", "actionStatus", "created")

    def get_type(self, obj):
        return "JoinAction"

    def get_agent(self, obj):
        return {"type": "Person", "name": obj.participant_name, "url": obj.actor}

    def get_object(self, obj):
        return DeedSerializer(obj.deed).data


class RemoteDeedSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    startDate = serializers.DateTimeField(source="start_date")
    endDate = serializers.DateTimeField(source="end_date")
    eventStatus = serializers.CharField(source="status")
    maximumAttendeeCapacity = serializers.IntegerField(source="max_attendees")
    organizer = serializers.SerializerMethodField()

    class Meta:
        model = RemoteDeed
        fields = (
            "type",
            "name",
            "description",
            "startDate",
            "endDate",
            "eventStatus",
            "maximumAttendeeCapacity",
            "organizer",
        )

    def get_type(self, obj):
        return "Event"

    def get_organizer(self, obj):
        return {"type": "Person", "name": obj.organizer_name, "url": obj.organizer_url}
