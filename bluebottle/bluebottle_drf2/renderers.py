from collections import OrderedDict

from django.contrib.auth.models import AnonymousUser
from django.utils import encoding

from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api import utils


class BluebottleJSONAPIRenderer(JSONRenderer):
    def get_indent(self, *args, **kwargs):
        return 4

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
