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

    def publish(self, event, actor):
        data = ActivityPubSerializer().to_representation(event)
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


adapter = JSONLDAdapter()
