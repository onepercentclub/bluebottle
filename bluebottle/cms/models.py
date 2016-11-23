from django.utils.translation import ugettext_lazy as _
from django.db import models

from feincms.admin.item_editor import FeinCMSInline
from feincms.module.page.models import Page
from feincms.contents import RichTextContent
from feincms.module.medialibrary.contents import MediaFileContent

from bluebottle.projects.models import Project

Page.register_extensions(
    'feincms.extensions.datepublisher',
    'feincms.extensions.translations',
)  # Example set of extensions

Page.register_templates({
    'title': _('Standard template'),
    'path': 'base.html',
    'regions': (
        ('main', _('Main content area')),
    ),
})

Page.create_content_type(RichTextContent)
Page.create_content_type(MediaFileContent, TYPE_CHOICES=(
    ('default', _('default')),
    ('lightbox', _('lightbox')),
))


class ProjectContentInline(FeinCMSInline):
    raw_id_fields = ('project',)


class ProjectContent(models.Model):
    project = models.ForeignKey(Project)

    feincms_item_editor_inline = ProjectContentInline

    class Meta:
        abstract = True # Required by FeinCMS, content types must be abstract


Page.create_content_type(ProjectContent)
