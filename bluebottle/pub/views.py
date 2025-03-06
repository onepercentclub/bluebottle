from django.http import JsonResponse
from rest_framework import viewsets

from .models import Platform
from .serializers import PlatformActivityPubSerializer


class ActivityPubViewSet(viewsets.ViewSet):
    def get_actor(self, request):
        """Return the Actor object for this instance"""
        platform = Platform.objects.get(domain=request.get_host())
        serializer = PlatformActivityPubSerializer(platform, context={'request': request})
        return JsonResponse(
            serializer.data,
            content_type='application/activity+json'
        )

    def get_outbox(self, request):
        """Return the Outbox collection"""
        # Get all published activities
        activities = []

        return JsonResponse({
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "OrderedCollection",
            "totalItems": len(activities),
            "orderedItems": activities
        }, content_type='application/activity+json')
