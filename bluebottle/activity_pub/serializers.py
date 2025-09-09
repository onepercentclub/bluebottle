import requests
import inflection
from urllib.parse import urlparse
from pyld import jsonld, ContextResolver
from cachetools import LRUCache

from rest_framework.reverse import reverse
from rest_framework import serializers
from rest_framework_json_api.serializers import Serializer

from django.urls import resolve

from bluebottle.clients import properties
from bluebottle.activity_pub.models import Person, Inbox, Outbox, PublicKey, Follow


processor = jsonld.JsonLdProcessor()
default_context = ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1']
processed_context = processor.process_context(
    processor._get_initial_context({}),
    {"@context": default_context},
    {
        'contextResolver': ContextResolver(LRUCache(maxsize=1000), jsonld.requests_document_loader())
    }
)


def is_local(url):
    return urlparse(url).hostname == properties.tenant.domain_url


def expand_iri(iri):
    return processor._expand_iri(processed_context, iri, vocab=True)


class RelatedJSONLDField(serializers.Field):
    def __init__(self, serializer_class):
        super().__init__()
        self.serializer_class = serializer_class

    def to_representation(self, instance):
        return self.serializer_class(
            context=self.parent.context, parent=self.parent
        ).to_representation(instance)

    def to_internal_value(self, data):
        model = self.serializer_class.Meta.model
        url = data['@id']

        if is_local(url):
            return model.objects.get(**resolve(urlparse(url).path).kwargs)
        else:
            serializer = self.serializer_class(context=self.context, data=data)
            serializer.is_valid()

            return serializer.save()


class RelatedIdField(serializers.Field):
    def __init__(self, *args, **kwargs):
        self.serializer_class = kwargs.pop('serializer_class')

        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        if instance.url is not None:
            url = instance.url
        else:
            url = reverse(
                instance.type,
                args=[instance.pk],
                request=self.context.get('request')
            )

        return {'@id': url}

    def to_internal_value(self, data):
        model = self.serializer_class.Meta.model
        url = data.pop('@id')

        if is_local(url):
            return model.objects.get(**resolve(urlparse(url).path).kwargs)
        else:
            response = requests.get(url)
            serializer = self.serializer_class(context=self.context, data=response.json())

            serializer.is_valid()

            return serializer.save()


class IdField(serializers.URLField):

    def to_representation(self, instance):
        if instance.url is not None:
            return instance.url
        else:
            url = reverse(
                instance.type,
                args=[instance.pk],
                request=self.context.get('request')
            )

            return url


class TypeField(serializers.URLField):
    def to_representation(self, instance):
        return instance.type


class ActivityPubSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        parent = kwargs.pop('parent', None)

        super().__init__(*args, **kwargs)

        self.parent = parent

        self.fields['@id'] = IdField(source='*')
        if not self.parent:
            self.fields['@type'] = TypeField(source='*')

    def to_representation(self, instance):
        result = dict(
            (expand_iri(inflection.camelize(key, False)), value)
            for key, value in super().to_representation(instance).items()
        )

        if self.parent:
            return result
        else:
            return processor.compact(
                result,
                default_context,
                {}
            )

    def to_internal_value(self, data):
        expanded = processor.expand(data, {})[0]

        if '@type' in expanded and expanded['@type'][0] != expand_iri(self.Meta.model.type):
            raise Exception(f'{self.__class__}: Wrong type: Expected {self.Meta.model.type}, got {expanded["@type"]}')

        result = {'url': expanded['@id']}

        for field_name, field in self.fields.items():
            iri = expand_iri(inflection.camelize(field_name, False))

            if iri in expanded:
                for value in expanded[iri]:
                    if '@value' in value:
                        result[field_name] = value['@value']
                    elif '@id' in value:
                        result[field_name] = field.to_internal_value(value)

        return result

    class Meta:
        exclude = ('id', 'polymorphic_ctype', 'url')


class InboxSerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        model = Inbox


class OutboxSerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        model = PublicKey


class PersonSerializer(ActivityPubSerializer):
    inbox = RelatedIdField(serializer_class=InboxSerializer)
    outbox = RelatedIdField(serializer_class=OutboxSerializer)
    public_key = RelatedJSONLDField(serializer_class=PublicKeySerializer)

    class Meta(ActivityPubSerializer.Meta):
        model = Person
        exclude = ActivityPubSerializer.Meta.exclude + ('member', )


class FollowSerializer(ActivityPubSerializer):
    actor = RelatedIdField(serializer_class=PersonSerializer)
    object = RelatedIdField(serializer_class=PersonSerializer)

    class Meta(ActivityPubSerializer.Meta):
        model = Follow


class FollowJSONAPISerializer(Serializer):
    url = serializers.CharField(required=False)

    class Meta(object):
        fields = (
            'id', 'url',
        )

    class JSONAPIMeta(object):
        resource_name = 'activity-pub-follows'
