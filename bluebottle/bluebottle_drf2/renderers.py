from django.db.models import Manager
from django.contrib.auth.models import AnonymousUser
from django.utils import encoding

from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api import utils

import copy
from collections import OrderedDict

import inflection
from rest_framework import relations
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings

from rest_framework_json_api.relations import (
    ResourceRelatedField,
)


class BluebottleJSONAPIRenderer(JSONRenderer):
    def get_indent(self, *args, **kwargs):
        return 4

    def extract_included(
        cls, fields, resource, resource_instance, included_resources, included_cache
    ):
        """
        Adds related data to the top level included key when the request includes
        ?include=example,example_field2
        """
        # this function may be called with an empty record (example: Browsable Interface)
        if not resource_instance:
            return

        current_serializer = fields.serializer
        context = current_serializer.context

        included_serializers = getattr(
            current_serializer, "included_serializers", dict()
        )
        included_resources = copy.copy(included_resources)
        included_resources = [
            inflection.underscore(value) for value in included_resources
        ]

        for field_name, field in iter(fields.items()):
            # Skip URL field
            if field_name == api_settings.URL_FIELD_NAME:
                continue

            # Skip fields without relations
            if not isinstance(
                field, (relations.RelatedField, relations.ManyRelatedField)
            ):
                continue

            try:
                included_resources.remove(field_name)
            except ValueError:
                # Skip fields not in requested included resources
                # If no child field, directly continue with the next field
                if field_name not in [
                    node.split(".")[0] for node in included_resources
                ]:
                    continue

            relation_instance = cls.extract_relation_instance(field, resource_instance)
            if isinstance(relation_instance, Manager):
                relation_instance = relation_instance.all()

            serializer_data = resource.get(field_name)

            if isinstance(field, relations.ManyRelatedField):
                serializer_class = included_serializers[field_name]
                field = serializer_class(relation_instance, many=True, context=context)
                serializer_data = field.data

            if isinstance(field, relations.RelatedField):
                if relation_instance is None or not serializer_data:
                    continue

                many = field._kwargs.get("child_relation", None) is not None

                if isinstance(field, ResourceRelatedField) and not many:
                    already_included = (
                        serializer_data["type"] in included_cache
                        and serializer_data["id"]
                        in included_cache[serializer_data["type"]]
                        and not [
                            field for field in included_resources if field.startswith(f'{field_name}.')
                        ]
                    )

                    if already_included:
                        continue

                serializer_class = included_serializers[field_name]
                field = serializer_class(relation_instance, many=many, context=context)
                serializer_data = field.data

            new_included_resources = [
                key.replace("%s." % field_name, "", 1)
                for key in included_resources
                if field_name == key.split(".")[0]
            ]

            if isinstance(field, ListSerializer):
                serializer = field.child
                relation_type = utils.get_resource_type_from_serializer(serializer)
                relation_queryset = list(relation_instance)

                if serializer_data:
                    for position in range(len(serializer_data)):
                        serializer_resource = serializer_data[position]
                        nested_resource_instance = relation_queryset[position]

                        resource_type = (
                            serializer_resource.get('type')
                            or utils.get_resource_type_from_instance(
                                nested_resource_instance
                            )
                            or relation_type
                        )
                        serializer_fields = utils.get_serializer_fields(
                            serializer.__class__(
                                nested_resource_instance, context=serializer.context
                            )
                        )

                        new_item = cls.build_json_resource_obj(
                            serializer_fields,
                            serializer_resource,
                            nested_resource_instance,
                            resource_type,
                            serializer,
                            getattr(serializer, "_poly_force_type_resolution", False),
                        )

                        try:
                            included_cache[new_item["type"]][new_item["id"]] = new_item
                        except TypeError:
                            pass

                        cls.extract_included(
                            serializer_fields,
                            serializer_resource,
                            nested_resource_instance,
                            new_included_resources,
                            included_cache,
                        )

            if isinstance(field, Serializer):
                relation_type = utils.get_resource_type_from_serializer(field)

                # Get the serializer fields
                serializer_fields = utils.get_serializer_fields(field)
                if serializer_data:
                    new_item = cls.build_json_resource_obj(
                        serializer_fields,
                        serializer_data,
                        relation_instance,
                        relation_type,
                        field,
                        getattr(field, "_poly_force_type_resolution", False),
                    )
                    included_cache[new_item["type"]][new_item["id"]] = new_item

                    cls.extract_included(
                        serializer_fields,
                        serializer_data,
                        relation_instance,
                        new_included_resources,
                        included_cache,
                    )

    @classmethod
    def build_json_resource_obj(
        cls,
        fields,
        resource,
        resource_instance,
        resource_name,
        *args,
        **kwargs
    ):
        if isinstance(resource_instance, AnonymousUser):
            return {
                'id': resource['id'],
                'type': resource_name,
                'attributes': {
                    'is-anonymous': True
                }
            }
        return super().build_json_resource_obj(
            fields, resource, resource_instance, resource_name, *args, **kwargs
        )


class ElasticSearchJSONAPIRenderer(BluebottleJSONAPIRenderer):
    @classmethod
    def build_json_resource_obj(
        cls,
        fields,
        resource,
        resource_instance,
        resource_name,
        serializer,
        force_type_resolution=False,
    ):
        """
        Builds the resource object (type, id, attributes) and extracts relationships.
        """
        # Determine type from the instance if the underlying model is polymorphic
        if force_type_resolution:
            resource_name = utils.get_resource_type_from_instance(resource_instance)

        resource_data = [
            ("type", resource_name),
            (
                "id",
                encoding.force_str(resource_instance.meta.id)
            ),
            ("attributes", cls.extract_attributes(fields, resource)),
        ]

        meta = cls.extract_meta(serializer, resource)
        if meta:
            resource_data.append(("meta", utils.format_field_names(meta)))

        return OrderedDict(resource_data)
