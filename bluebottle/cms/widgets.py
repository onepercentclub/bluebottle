from __future__ import absolute_import, unicode_literals

import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser

from bluebottle.projects.models import Project


class AdminProjectChooser(AdminChooser):
    choose_one_text = _('Choose a project')
    choose_another_text = _('Choose another project')
    model = Project

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.model, value)
        original_field_html = super(AdminProjectChooser, self).render_html(name, value, attrs)

        return render_to_string("cms/widgets/project_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'project': instance,
        })

    def render_js_init(self, id, name, value):
        return "createProjectChooser({0});".format(json.dumps(id))
