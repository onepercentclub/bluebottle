import logging

from bluebottle.activity_pub.serializers import (
    ActivityPubSerializer, FederatedObjectSerializer
)
from bluebottle.webfinger.client import client as webfinger_client


class JSONLDAdapter():
    def discover(self, url):
        from bluebottle.activity_pub.clients import client
        discovered_url = webfinger_client.get(url)
        data = client.fetch(discovered_url)

        serializer = ActivityPubSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return serializer.save()

    def publish(self, activity, actor):
        data = ActivityPubSerializer().to_representation(activity)
        from bluebottle.activity_pub.clients import client
        client.post(actor.inbox.iri, data=data)

    def adopt(self, instance, **kwargs):
        serializer = FederatedObjectSerializer(
            data=ActivityPubSerializer(instance=instance).data
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(**kwargs)

    def sync(self, model):
        if hasattr(model, 'origin') and model.origin:
            instance = model.origin
        else:
            instance = None

        serializer = ActivityPubSerializer(
            data=FederatedObjectSerializer(model).data,
            instance=instance,
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(federated_object=model)

    def link(self, event, request=None):
        from bluebottle.activity_links.serializers import LinkedActivitySerializer

        serializer = LinkedActivitySerializer(
            data=ActivityPubSerializer(instance=event).data,
            instance=event.linked_activity,
        )
        serializer.is_valid(raise_exception=True)

        return serializer.save(
            host_organization=event.source.federation_object,
            event=event
        )


adapter = JSONLDAdapter()
