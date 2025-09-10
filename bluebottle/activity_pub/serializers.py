import inflection
from urllib.parse import urlparse
from django.db import connection, models

from rest_framework.reverse import reverse
from rest_framework import serializers

from django.urls import resolve

from bluebottle.clients import properties
from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept
)
from bluebottle.activity_pub.adapters import (
    adapter, processor, default_context, processed_context
)


def is_local(url):
    return urlparse(url).hostname == properties.tenant.domain_url


def expand_iri(iri):
    return processor._expand_iri(processed_context, iri, vocab=True)


class RelatedJSONLDField(serializers.Field):
    def __init__(self, serializer_class, url_name):
        super().__init__()
        self.serializer_class = serializer_class
        self.url_name = url_name

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
        self.url_name = kwargs.pop('url_name')

        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        if instance.url is not None:
            url = instance.url
        else:
            url = connection.tenant.build_absolute_url(
                reverse(
                    self.url_name,
                    args=[instance.pk],
                )
            )
        return {'@id': url}

    def to_internal_value(self, data):
        model = self.serializer_class.Meta.model
        url = data.pop('@id')

        if is_local(url):
            return model.objects.get(**resolve(urlparse(url).path).kwargs)
        else:
            return adapter.sync(url, self.serializer_class)


class IdField(serializers.URLField):
    def to_representation(self, instance):
        if instance.url is not None:
            return instance.url
        else:
            url = connection.tenant.build_absolute_url(
                reverse(
                    self.parent.Meta.url_name,
                    args=[instance.pk],
                )
            )

            return url


class TypeField(serializers.URLField):
    def to_representation(self, instance):
        return self.parent.Meta.type


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

        if '@type' in expanded and expanded['@type'][0] != expand_iri(self.Meta.type):
            raise Exception(f'{self.__class__}: Wrong type: Expected {self.Meta.type}, got {expanded["@type"]}')

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
        type = 'Inbox'
        model = Inbox
        url_name = 'json-ld:inbox'


class OutboxSerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        type = 'Outbox'
        url_name = 'json-ld:outbox'
        model = Outbox


class PublicKeySerializer(ActivityPubSerializer):
    class Meta(ActivityPubSerializer.Meta):
        type = 'Outbox'
        url_name = 'json-ld:public-key'
        model = PublicKey


class PersonSerializer(ActivityPubSerializer):
    inbox = RelatedIdField(serializer_class=InboxSerializer, url_name="json-ld:inbox")
    outbox = RelatedIdField(serializer_class=OutboxSerializer, url_name="json-ld:outbox")
    public_key = RelatedJSONLDField(serializer_class=PublicKeySerializer, url_name="json-ld:public-key")

    class Meta(ActivityPubSerializer.Meta):
        type = 'Person'
        url_name = 'json-ld:person'
        exclude = ActivityPubSerializer.Meta.exclude + ('member', )
        model = Person


class BaseActivitySerializer(ActivityPubSerializer):
    actor = RelatedIdField(serializer_class=PersonSerializer, url_name="json-ld:person")


class FollowSerializer(BaseActivitySerializer):
    object = RelatedIdField(serializer_class=PersonSerializer, url_name="json-ld:follow")

    class Meta(ActivityPubSerializer.Meta):
        type = 'Follow'
        url_name = 'json-ld:follow'
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    object = RelatedIdField(serializer_class=FollowSerializer, url_name="json-ld:accept")

    class Meta(ActivityPubSerializer.Meta):
        type = 'Accept'
        url_name = 'json-ld:accept'
        model = Accept


class ActivitySerializer(serializers.Serializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer
    ]

    def __init__(self, *args, **kwargs):
        self._serializers = [
            serializer(*args, **kwargs) for serializer in self.polymorphic_serializers
        ]
        super().__init__(*args, **kwargs)

    def get_serializer(self, data):
        if isinstance(data, models.Model):
            for serializer in self._serializers:
                if serializer.Meta.model == data.__class__:
                    return serializer
        else:
            compacted = processor.compact(data, default_context, [])

            for serializer in self._serializers:
                if compacted['type'] == serializer.Meta.type:
                    return serializer

    def to_representation(self, instance):
        return self.get_serializer(instance).to_representation(instance)

    def to_internal_value(self, data):
        return self.get_serializer(data).to_internal_value(data)

    def create(self, validated_data):
        return self.get_serializer(self.initial_data).create(validated_data)

    def update(self, instance, validated_data):
        return self.get_serializer(instance).update(validated_data)

    def is_valid(self, *args, **kwargs):
        super().is_valid(*args, **kwargs)

        if hasattr(self, 'instance') and self.instance:
            serializer = self.get_serializer(self.instance)
        else:
            serializer = self.get_serializer(self.initial_data)

        return serializer.is_valid(*args, **kwargs)
