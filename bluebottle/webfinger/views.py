import re
from rest_framework import generics, renderers, serializers, exceptions

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.activity_pub.serializers.base import ActivityPubSerializer


class WebFingerRenderer(renderers.JSONRenderer):
    media_type = 'application/jrd+json'


def to_webfinger(actor):
    data = ActivityPubSerializer().to_representation(actor)
    return {
        'subject': actor.webfinger_uri,
        'aliases': [data['id']],
        'links': [{
            'rel': 'self',
            'type': "application/activity+json",
            'href': data['id']
        }]

    }


class WebFingerSerializer(serializers.Serializer):
    def to_representation(self, obj):
        data = ActivityPubSerializer().to_representation(obj)
        return {
            'subject': obj.webfinger_uri,
            'aliases': [data['id']],
            'links': [{
                'rel': 'self',
                'type': "application/activity+json",
                'href': data['id']
            }]

        }


class WebFingerView(generics.RetrieveAPIView):
    renderer_classes = [WebFingerRenderer]
    serializer_class = WebFingerSerializer

    def get_object(self):
        try:
            resource = self.request.GET['resource']
        except KeyError:
            raise exceptions.ValidationError()

        if re.match(f'{self.request.scheme}://{self.request.get_host()}/?$', resource):
            settings = SitePlatformSettings.load()

            if settings.organization and hasattr(settings.organization, 'origin'):
                return settings.organization.origin

        raise exceptions.NotFound()
