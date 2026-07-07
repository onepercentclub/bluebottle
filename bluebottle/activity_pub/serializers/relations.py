import requests
from urllib.parse import urlparse

from django.db import models
from rest_framework.relations import RelatedField, ManyRelatedField
from rest_framework.exceptions import ValidationError

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.serializers import ActivityPubSerializer, FederatedObjectSerializer
from bluebottle.activity_pub.clients import client
from bluebottle.activity_pub.utils import iri_from_data, is_local, resource_type_from_iri


class ManyResourceRelatedField(ManyRelatedField):
    def to_internal_value(self, data):
        if not isinstance(data, (tuple, list)):
            data = [data]

        return super().to_internal_value(data)

    def get_related_origin(self):
        origin = self.parent.origin
        if origin:
            serializer = FederatedObjectSerializer()._get_serializer_from_model_or_instance(
                origin
            )
            source = serializer.fields[self.source].source
            return getattr(origin, source).all()
        else:
            return []

    def save(self, validated_data):
        related_origin = self.get_related_origin()

        return [
            self.child_relation.save(
                item, origin=related_origin[index] if index < len(related_origin) else None
            ) for index, item in enumerate(validated_data)
        ]


class RelatedResourceField(RelatedField):
    def __init__(self, type, include=False, *args, **kwargs):
        self.include = include
        self.type = type
        super().__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, type, include, *args, **kwargs):
        kwargs['child_relation'] = cls(type, include)
        return ManyResourceRelatedField(*args, **kwargs)

    def get_queryset(self):
        return ActivityPubModel.objects.all()

    def to_representation(self, value):
        return ActivityPubSerializer(
            full=False, include=self.include
        ).to_representation(value)

    def _get_request_auth(self):
        parent = self.parent
        while parent:
            context = getattr(parent, 'context', None)
            if context:
                request = context.get('request')
                if request:
                    return getattr(request, 'auth', None)
            parent = getattr(parent, 'parent', None)
        return None

    def _allowed_types(self):
        if isinstance(self.type, str):
            return [self.type]
        if isinstance(self.type, (tuple, list)):
            return list(self.type)
        return []

    def _infer_type(self, data):
        if 'type' in data:
            return data

        allowed = self._allowed_types()
        if len(allowed) == 1:
            return dict(type=allowed[0], **data)

        iri = iri_from_data(data)
        if iri:
            resource_type = resource_type_from_iri(iri, allowed)
            if resource_type:
                result = dict(type=resource_type, **data)
                if resource_type in ('Organization', 'Person') and not result.get('name'):
                    result['name'] = urlparse(iri).hostname or resource_type
                return result

        return data

    def _representation_for_iri(self, iri):
        instance = ActivityPubModel.objects.from_iri(iri)
        if instance:
            return ActivityPubSerializer(instance=instance).data

        request_auth = self._get_request_auth()
        auth_iri = getattr(request_auth, 'iri', None)
        if request_auth and auth_iri and auth_iri == iri:
            return ActivityPubSerializer(instance=request_auth).data

        return None

    def _stub_from_iri(self, iri):
        allowed = self._allowed_types()
        resource_type = resource_type_from_iri(iri, allowed)
        if not resource_type:
            return None

        stub = {'type': resource_type, 'id': iri}
        if resource_type in ('Organization', 'Person'):
            stub['name'] = urlparse(iri).hostname or resource_type

        return stub

    def _fetch_remote(self, iri):
        try:
            fetched = client.fetch(iri)
        except requests.HTTPError:
            fetched = None

        if fetched:
            if 'type' not in fetched:
                fetched = self._infer_type(fetched)
            return fetched

        return self._stub_from_iri(iri)

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'id': data}

        if isinstance(data, dict) and 'id' not in data and 'iri' in data:
            data = dict(data, id=data['iri'])

        data = self._infer_type(data)
        serializer = ActivityPubSerializer()

        try:
            return serializer.to_internal_value(data)
        except ValidationError:
            iri = iri_from_data(data)
            if not iri:
                raise

            data = self._infer_type(data)
            try:
                return serializer.to_internal_value(data)
            except ValidationError:
                pass

            representation = self._representation_for_iri(iri)
            if representation:
                return serializer.to_internal_value(representation)

            if is_local(iri):
                stub = self._stub_from_iri(iri)
                if stub:
                    return serializer.to_internal_value(stub)
                raise

            fetched_data = self._fetch_remote(iri)
            if fetched_data:
                return serializer.to_internal_value(fetched_data)

            raise

    def get_related_origin(self):
        try:
            origin = self.parent.origin
            if origin:
                serializer = FederatedObjectSerializer()._get_serializer_from_model_or_instance(
                    origin
                )
                source = serializer.fields[self.source].source
                related_origin = getattr(origin, source)

                if isinstance(related_origin, models.Model):
                    return related_origin
            else:
                return None
        except AttributeError:
            pass

    def save(self, value, origin=None):
        if value is not None:
            serializer = ActivityPubSerializer(
                data=value,
                origin=origin or self.get_related_origin()
            )

            iri = iri_from_data(value)
            resource_type = value.get('type')
            if iri and resource_type:
                model_class = serializer.resource_type_model_mapping[resource_type]
                serializer.instance = model_class.objects.from_iri(iri)

            serializer._validated_data = value
            serializer._errors = []
            return serializer.save()
