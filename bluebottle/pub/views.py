from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response

from bluebottle.deeds.models import Deed

from .models import ActivityPubRegistration, Platform, RemoteDeed
from .renderers import JSONLDRenderer
from .serializers import (
    ActivityPubRegistrationSerializer,
    DeedSerializer,
    PlatformActivityPubSerializer,
)
from .utils import fetch_actor_profile


class ActivityPubViewSet(viewsets.ViewSet):
    renderer_classes = [JSONLDRenderer]

    def get_actor(self, request):
        """Return the Actor object for this instance"""
        platform = Platform.objects.get(domain=request.get_host())
        serializer = PlatformActivityPubSerializer(
            platform, context={"request": request}
        )
        return JsonResponse(serializer.data, content_type="application/activity+json")

    def get_outbox(self, request):
        """Return the Outbox collection"""
        # Get all published activities
        activities = []

        return JsonResponse(
            {
                "@context": "https://www.w3.org/ns/activitystreams",
                "type": "OrderedCollection",
                "totalItems": len(activities),
                "orderedItems": activities,
            },
            content_type="application/activity+json",
        )

    def get_registrations(self, request):
        deed_id = request.query_params.get("deed")
        deed = get_object_or_404(Deed, pk=deed_id)
        registrations = ActivityPubRegistration.objects.filter(deed=deed)

        response_data = {
            "@context": "https://schema.org",
            "@type": "Event",
            **DeedSerializer(deed).data,
            "participant": [
                {
                    "@type": "Person",
                    "name": reg.participant_name,
                    "potentialAction": {
                        "@type": "JoinAction",
                        "actionStatus": reg.status,
                        "target": {"@type": "EntryPoint", "urlTemplate": reg.actor},
                    },
                }
                for reg in registrations
            ],
            "userInteractionCount": {
                "@type": "InteractionCounter",
                "interactionType": "https://schema.org/JoinAction",
                "userInteractionCount": registrations.count(),
            },
        }

        return Response(response_data)

    def add_registration(self, request):
        deed_id = request.query_params.get("deed")
        deed = get_object_or_404(Deed, pk=deed_id)

        # Verify the activity type is 'JoinAction'
        if request.data.get("@type") != "JoinAction":
            return Response(
                {"error": "Invalid activity type"}, status=status.HTTP_400_BAD_REQUEST
            )

        agent = request.data.get("agent", {})
        if not agent.get("url"):
            return Response(
                {"error": "Agent URL is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get the actor's inbox from their profile
        actor_profile = fetch_actor_profile(agent["url"])
        if not actor_profile or "inbox" not in actor_profile:
            return Response(
                {"error": "Could not fetch actor profile"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = ActivityPubRegistration.objects.create(
            deed=deed,
            actor=agent["url"],
            inbox=actor_profile["inbox"],
            participant_name=agent.get("name", ""),
            status="https://schema.org/CompletedActionStatus",
        )

        serializer = ActivityPubRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def inbox(self, request):
        """Handle incoming ActivityPub messages."""
        data = request.data

        # Verify the activity type
        activity_type = data.get("type")
        if activity_type not in ["Create", "Update", "Delete"]:
            return Response(
                {"error": "Unsupported activity type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the actual event object
        event = data.get("object", {})
        if event.get("type") != "Event":
            return Response(
                {"error": "Invalid object type"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get or verify the platform
        try:
            platform = Platform.objects.get(actor_url=data.get("actor"))
        except Platform.DoesNotExist:
            return Response(
                {"error": "Unknown platform"}, status=status.HTTP_403_FORBIDDEN
            )

        if activity_type == "Delete":
            RemoteDeed.objects.filter(remote_id=event.get("id")).delete()
            return Response(status=status.HTTP_200_OK)

        # Parse the event data
        deed_data = {
            "remote_id": event.get("id"),
            "platform": platform,
            "name": event.get("name"),
            "description": event.get("description", ""),
            "start_date": datetime.fromisoformat(
                event.get("startDate").replace("Z", "+00:00")
            ),
            "end_date": datetime.fromisoformat(
                event.get("endDate").replace("Z", "+00:00")
            ),
            "status": event.get("eventStatus", "https://schema.org/EventScheduled"),
            "max_attendees": event.get("maximumAttendeeCapacity"),
            "organizer_name": event.get("organizer", {}).get("name", ""),
            "organizer_url": event.get("organizer", {}).get("url", ""),
        }

        # Create or update the deed
        deed, created = RemoteDeed.objects.update_or_create(
            remote_id=deed_data["remote_id"], defaults=deed_data
        )

        return Response(status=status.HTTP_200_OK)
