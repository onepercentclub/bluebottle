from rest_framework_json_api.renderers import JSONRenderer
from django.contrib.auth.models import AnonymousUser


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
