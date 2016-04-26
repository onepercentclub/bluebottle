from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.utils.model_dispatcher import get_project_model
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.generic import View
from django.utils import timezone
from django.utils import translation
import json

PROJECT_MODEL = get_project_model()


class WidgetView(View):
    template = "widget/widget.html"

    def get(self, request, *args, **kwargs):

        # Save the current language
        cur_language = translation.get_language()
        callback = request.GET.get('callback', None)

        id = request.GET.get('id', None)
        size = request.GET.get('size', None)
        height = request.GET.get('height', None)
        width = request.GET.get('width', None)
        widget = request.GET.get('widget', 'project')

        partner = request.GET.get('partner', None)
        project_slug = request.GET.get('project', None)

        language = request.GET.get('language', None)

        if language:
            # Activate the language sent by the widget
            translation.activate(language)

        projects = None
        now = timezone.now()

        allowed_phases = ProjectPhase.objects.filter(
            slug__in=['running', 'campaign'])

        if project_slug:
            try:
                projects = PROJECT_MODEL.objects.filter(slug=project_slug)
            except PROJECT_MODEL.DoesNotExist:
                pass
        else:
            projects = PROJECT_MODEL.objects.filter(deadline__gt=now).order_by(
                '?')[:3]

        if 'localhost' in request.get_host():
            host = 'http://' + request.get_host()
        else:
            host = 'https://' + request.get_host()

        html = render_to_string(self.template, locals())

        # Re-activate the previous language
        translation.activate(cur_language)
        response_data = "%s ( {'html': %s } )" % (callback, json.dumps(html))
        return HttpResponse(response_data, content_type="text/javascript")
