import copy

import inflection

from django.db.models import Manager
from django.utils import six

from rest_framework import relations
from rest_framework.serializers import (
    BaseSerializer, ListSerializer, Serializer
)
from rest_framework.settings import api_settings

from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api import utils
from rest_framework_json_api.relations import ResourceRelatedField


class BluebottleJSONAPIRenderer(JSONRenderer):
    def get_indent(self, *args, **kwargs):
        return 4

    @classmethod
    def extract_included(cls, fields, resource, resource_instance, included_resources,
                         included_cache):
        """
        Adds related data to the top level included key when the request includes
        ?include=example,example_field2
        """
        # this function may be called with an empty record (example: Browsable Interface)
        if not resource_instance:
            return

        current_serializer = fields.serializer
        context = current_serializer.context
        included_serializers = utils.get_included_serializers(current_serializer)
        included_resources = copy.copy(included_resources)
        included_resources = [inflection.underscore(value) for value in included_resources]

        for field_name, field in six.iteritems(fields):
            # Skip URL field
            if field_name == api_settings.URL_FIELD_NAME:
                continue

            # Skip fields without relations or serialized data
            if not isinstance(
                    field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)
            ):
                continue

            try:
                included_resources.remove(field_name)
            except ValueError:
                # Skip fields not in requested included resources
                # If no child field, directly continue with the next field
                if field_name not in [node.split('.')[0] for node in included_resources]:
                    continue

            relation_instance = cls.extract_relation_instance(
                field, resource_instance
            )
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

                many = field._kwargs.get('child_relation', None) is not None

                if isinstance(field, ResourceRelatedField) and not many:
                    already_included = serializer_data['type'] in included_cache and \
                        serializer_data['id'] in included_cache[serializer_data['type']]

                    if already_included:
                        continue

                serializer_class = included_serializers[field_name]
                field = serializer_class(relation_instance, many=many, context=context)
                serializer_data = field.data

            new_included_resources = [key.replace('%s.' % field_name, '', 1)
                                      for key in included_resources
                                      if field_name == key.split('.')[0]]

            if isinstance(field, ListSerializer):
                serializer = field.child
                relation_type = utils.get_resource_type_from_serializer(serializer)
                relation_queryset = list(relation_instance)

                if serializer_data:
                    for position in range(len(serializer_data)):
                        serializer_resource = serializer_data[position]
                        nested_resource_instance = relation_queryset[position]
                        resource_type = (
                            relation_type or
                            utils.get_resource_type_from_instance(nested_resource_instance)
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
                            getattr(serializer, '_poly_force_type_resolution', False)
                        )

                        # NEW: Add meta to included resource
                        meta = cls.extract_meta(serializer_class, serializer_resource)
                        if meta:
                            new_item.update({'meta': utils._format_object(meta)})

                        included_cache[new_item['type']][new_item['id']] = \
                            utils._format_object(new_item)
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
                new_item = cls.build_json_resource_obj(
                    serializer_fields,
                    serializer_data,
                    relation_instance,
                    relation_type,
                    getattr(field, '_poly_force_type_resolution', False)
                )
                # NEW: Add meta to included resource
                meta = cls.extract_meta(serializer_class, serializer_data)
                if meta:
                    new_item.update({'meta': utils._format_object(meta)})

                included_cache[new_item['type']][new_item['id']] = utils._format_object(
                    new_item
                )
                cls.extract_included(
                    serializer_fields,
                    serializer_data,
                    relation_instance,
                    new_included_resources,
                    included_cache,
                )
