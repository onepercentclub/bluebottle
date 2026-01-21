from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from bluebottle.activity_pub.processor import (
    processed_context, processor, default_context
)
from bluebottle.activity_pub.models import Triple


class ResourceMeta(type):
    registry = {}

    def __new__(cls, name, bases, attrs):
        result = super().__new__(cls, name, bases, attrs)
        if bases:
            if 'type' not in attrs:
                raise TypeError('Resource require a type attribute')

            iri = processor._expand_iri(processed_context, attrs['type'], None, True)
            cls.registry[iri] = result

        return result


class Resource(metaclass=ResourceMeta):
    type = None

    def __init__(self, document):
        self.iri = document['@id']
        self.document = document

    @classmethod
    def from_document(cls, document):
        expanded = processor.expand(document, {'expandContext': default_context})[0]

        resource_type = 'https://www.w3.org/ns/activitystreams#Organization'
        resource_cls = ResourceMeta.registry.get(resource_type, cls)

        return resource_cls(expanded)

    @classmethod
    def from_iri(cls, iri):
        triples = [
            {
                'subject': triple.subject,
                'predicate': triple.predicate,
                'object': triple.object,
            } for triple in Triple.objects.filter(subject__value=iri)
        ]
        if triples:
            document = processor.from_rdf({'@default': triples}, {})
        else:
            document = {'@id': iri, 'type': 'Link'}


        return cls.from_document(document)

    @property
    def rdf(self):
        return processor.to_rdf(self.document, {})['@default']

    @property
    def data(self):
        return dict(
            (
                triple['predicate']['value'],
                triple['object']
            ) for triple in self.rdf
        )

    def save(self):
        Triple.objects.filter(subject__value=self.iri).delete()

        for triple in self.rdf:
            if triple['subject']['value'] == self.iri:
                Triple.objects.create(
                    subject=triple['subject'],
                    predicate=triple['predicate'],
                    object=triple['object'],
                )

    def __getattr__(self, attr):
        try:
            iri = processor._expand_iri(processed_context, attr, None, True)
            object = self.data[iri]
            if object['type'] == 'literal':
                return object['value']
            else:
                if '@type' in self.document[iri][0]:
                   return Resource(self.document[iri][0])
                else:
                    return Resource.from_iri(
                        object['value']
                    )
        except KeyError:
            raise AttributeError(attr)

    def __str__(self):
        type = self.document['@type'][0]
        try:
            return f'{type}: {self.name}'
        except AttributeError:
            return f'{type}: {self.iri}'

    def __repr__(self):
        return f"<resource '{type(self).__name__}' '{self.iri}'>"


class Inbox(Resource):
    type = 'Inbox'


class Outbox(Resource):
    type = 'Outbox'


class PublicKey(Resource):
    type = 'PublicKey'

    def save(self):
        if not self.private_key:
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')


            self.public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            self.private_key = PrivateKey.create(private_key_pem=private_key_pem)
            self.private_key.save()


class PrivateKey(Resource):
    type = 'PrivateKey'


class Organization(Resource):
    type = 'Organization'

    def save(self):
        if not hasattr(self, 'inbox'):
            self.inbox = Inbox.create()
            self.inbox.save()

        if not hasattr(self, 'outbox'):
            self.outbox = Outbox.create()
            self.outbox.save()

        if not hasattr(self, 'publicKey'):
            self.public_key = PublicKey.create()
            self.public_key.save()

        super().save()
