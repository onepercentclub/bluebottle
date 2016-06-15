from wagtail.wagtailcore.blocks import ChooserBlock

from bluebottle.projects.models import Project
from bluebottle.cms.widgets import AdminProjectChooser


class ProjectChooserBlock(ChooserBlock):
    target_model = Project

    widget = AdminProjectChooser

    def render_basic(self, value):
        return value.title

    class Meta:
        icon = "image"
