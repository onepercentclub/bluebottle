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
        from bluebottle.activity_pub.models import Transition

        serializer = FederatedObjectSerializer(
            data=ActivityPubSerializer(instance=instance).data
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save(**kwargs)

        try:
            # Re-run all transitions that might have happened before the model was adopted
            for transition in Transition.objects.filter(object=instance):
                transition.save()
        except ValueError:
            pass

        return result

    def link(self, instance, **kwargs):
        from bluebottle.activity_links.serializers import LinkedActivitySerializer

        serializer = LinkedActivitySerializer(
            data=ActivityPubSerializer(instance=instance).data,
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(**kwargs)

    def sync(self, model):
        serializer = ActivityPubSerializer(
            data=FederatedObjectSerializer(model).data,
            origin=model
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()


adapter = JSONLDAdapter()
