from django_tools.middlewares.ThreadLocal import get_current_request
from rest_framework_json_api.renderers import JSONRenderer


class StatisticsRenderer(JSONRenderer):

    @classmethod
    def build_json_resource_obj(cls, *args, **kwargs):
        obj = super(StatisticsRenderer, cls).build_json_resource_obj(*args, **kwargs)
        req = get_current_request()
        if 'year' in req.GET:
            obj['id'] = obj['id'] + '-' + req.GET['year']
        return obj
