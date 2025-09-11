import inflection
from urllib.parse import urlparse

from bluebottle.utils.fields import RichTextField
from django.db import connection, models

from rest_framework.reverse import reverse
from rest_framework import serializers

from django.urls import resolve

from bluebottle.clients import properties
from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept, Event, Publish
)
from bluebottle.activity_pub.adapters import (
    adapter, processor, default_context, processed_context
)


def is_local(url):
    return urlparse(url).hostname == properties.tenant.domain_url


def expand_iri(iri):
    return processor._expand_iri(processed_context, iri, vocab=True)


class RelatedActivityPubField(serializers.Field):
    def __init__(self, serializer_class, *args, **kwargs):
        self.serializer_class = serializer_class
        self.include = kwargs.pop('include', False)

        super().__init__(*args, **kwargs)

    @property
    def url_name(self):
        return self.serializer_class.Meta.url_name

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

        if self.include:
            serializer = self.serializer_class()
            serializer.bind(parent=self.parent, field_name=self.field_name)

            representation = serializer.to_representation(instance)

            return representation
        else:
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
        super().__init__(*args, **kwargs)

        self.fields['@id'] = IdField(source='*')
        self.fields['@type'] = TypeField(source='*')

    def to_representation(self, instance):
        result = dict(
            (expand_iri(inflection.camelize(key, False)), value)
            for key, value in super().to_representation(instance).items()
        )

        if self.parent:
            del result['@type']
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
        type = 'PublicKey'
        url_name = 'json-ld:public-key'
        model = PublicKey


class PersonSerializer(ActivityPubSerializer):
    inbox = RelatedActivityPubField(InboxSerializer)
    outbox = RelatedActivityPubField(OutboxSerializer)
    public_key = RelatedActivityPubField(PublicKeySerializer, include=True)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Person'
        url_name = 'json-ld:person'
        exclude = ActivityPubSerializer.Meta.exclude + ('member', )
        model = Person


class EventSerializer(ActivityPubSerializer):
    organizer = RelatedActivityPubField(PersonSerializer)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    name = serializers.CharField()
    description = RichTextField()

    class Meta(ActivityPubSerializer.Meta):
        type = 'Event'
        url_name = 'json-ld:event'
        exclude = ActivityPubSerializer.Meta.exclude + ('activity', )
        model = Event


class BaseActivitySerializer(ActivityPubSerializer):
    actor = RelatedActivityPubField(PersonSerializer)


class FollowSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(PersonSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Follow'
        url_name = 'json-ld:follow'
        model = Follow


class AcceptSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(FollowSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Accept'
        url_name = 'json-ld:accept'
        model = Accept


class PublishSerializer(BaseActivitySerializer):
    object = RelatedActivityPubField(EventSerializer)

    class Meta(ActivityPubSerializer.Meta):
        type = 'Publish'
        url_name = 'json-ld:publish'
        model = Publish


class PolymorpphicActivityPubSerializer(serializers.Serializer):
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


class ActivitySerializer(PolymorpphicActivityPubSerializer):
    polymorphic_serializers = [
        FollowSerializer, AcceptSerializer, PublishSerializer
    ]
