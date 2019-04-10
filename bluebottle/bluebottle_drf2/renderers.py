from rest_framework_json_api.renderers import JSONRenderer


class BluebottleJSONAPIRenderer(JSONRenderer):
    def get_indent(self, *args, **kwargs):
        return 4
