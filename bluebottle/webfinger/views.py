import re
from rest_framework import generics, renderers, serializers, exceptions

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.activity_pub.serializers import ActorSerializer


class WebFingerRenderer(renderers.JSONRenderer):
    media_type = 'application/jrd+json'


def to_webfinger(actor):
    data = ActorSerializer().to_representation(actor)
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
        data = ActorSerializer().to_representation(obj)
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
        except IndexError:
            raise exceptions.ValidationError()

        if re.match(f'{self.request.scheme}://{self.request.get_host()}/?$', resource):
            settings = SitePlatformSettings.load()

            if settings.organization and hasattr(settings.organization, 'activity_pub_organization'):
                return settings.organization.activity_pub_organization

        raise exceptions.NotFound()
