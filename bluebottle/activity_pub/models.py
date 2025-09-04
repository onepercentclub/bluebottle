import inflection

from django.db import models

from pyld import jsonld

from polymorphic.models import PolymorphicModel

processor = jsonld.JsonLdProcessor()
MODEL_MAPPING = {}


def register(cls):
    iri = cls.expand_iri(cls.type)

    MODEL_MAPPING[iri] = cls

    return cls


class ActivityPubModel(PolymorphicModel):
    url = models.URLField()

    type = None

    context = {
        "as": "https://www.w3.org/ns/activitystreams#",
        "sec": "https://w3id.org/security#",
        "ldp": "http://www.w3.org/ns/ldp#",
        "Person": "as:Person",
        "name": "as:name",
        "inbox": {
            "@id": "ldp:inbox",
            "@type": "@id"
        },
        "outbox": {
            "@id": "as:outbox",
            "@type": "@id"
        },
        "privateKeyPem": "sec:privateKeyPem",
        "publicKeyPem": "sec:publicKeyPem",
        "publicKey": {"@id": "sec:publicKey", "@type": "@id"},
        "owner": {"@id": "sec:owner", "@type": "@id"},
    }

    def to_jsonld(self, include_type=True):
        data = {}

        if include_type:
            data['@type'] = self.__class__.expand_iri(self.type)

        for field in self._meta.fields:
            value = getattr(self, field.name)

            if field.name in ('id', 'polymorphic_ctype') or field.name.endswith('_ptr'):
                continue

            if field.name == 'url':
                data['@id'] = self.url
            else:
                if isinstance(value, ActivityPubModel):
                    data[
                        self.__class__.expand_iri(inflection.camelize(field.name, False))
                    ] = value.to_jsonld(include_type=False)
                else:
                    data[self.__class__.expand_iri(inflection.camelize(field.name, False))] = value

        if include_type:
            return processor.compact(
                data,
                ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
                {}
            )
        else:
            return data

    @classmethod
    def expand_iri(cls, iri):
        initial_context = processor._get_initial_context({})
        processed_context = processor.process_context(
            initial_context, cls.context, {}
        )

        return processor._expand_iri(processed_context, iri, vocab=True)

    @classmethod
    def save_graph(cls, graph, expand=True):
        if expand:
            expanded = processor.expand(graph, {})[0]

        else:
            expanded = graph

        if '@type' in expanded and expanded['@type'][0] != cls.expand_iri(cls.type):
            raise Exception('Wrong type')

        data = {'url': expanded['@id']}

        for field in cls._meta.fields:
            iri = cls.expand_iri(inflection.camelize(field.name, False))

            if iri in expanded:
                for value in expanded[iri]:
                    if '@value' in value:
                        data[field.name] = value['@value']
                    elif '@id' in value:
                        Model = field.related_model
                        related_instance = Model.save_graph(value, expand=False)

                        data[field.name] = related_instance

        instance = cls(**data)
        instance.save()

        return instance


@register
class Actor(ActivityPubModel):
    type = 'Actor'

    inbox = models.ForeignKey('activity_pub.Inbox', on_delete=models.CASCADE)
    outbox = models.ForeignKey('activity_pub.Outbox', on_delete=models.CASCADE)
    public_key = models.ForeignKey('activity_pub.PublicKey', on_delete=models.CASCADE)


@register
class Person(Actor):
    type = 'Person'

    name = models.TextField()


@register
class Inbox(ActivityPubModel):
    type = 'Inbox'


@register
class Outbox(ActivityPubModel):
    type = 'Outbox'


class Activity(ActivityPubModel):
    type = 'Activity'

    actor = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE, related_name='activities')
    to = models.ManyToManyField('activity_pub.Actor', related_name='recevied_activities')
    summary = models.TextField()


class Follow(Activity):
    type = 'Follow'

    object = models.ForeignKey('activity_pub.Actor', on_delete=models.CASCADE)


class PublicKey(ActivityPubModel):
    type = 'sec:PublicKey'

    public_key_pem = models.TextField()
