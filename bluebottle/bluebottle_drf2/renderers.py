from rest_framework_json_api.renderers import JSONRenderer
from bluebottle.members.models import Member
from django.contrib.auth.models import AnonymousUser


class BluebottleJSONAPIRenderer(JSONRenderer):
    def get_indent(self, *args, **kwargs):
        return 4

    @classmethod
    def extract_relation_instance(cls, field, resource_instance):
        result = super().extract_relation_instance(field, resource_instance)

        if isinstance(result, Member) and getattr(resource_instance, 'anonymized', False):
            return AnonymousUser()

        return result
