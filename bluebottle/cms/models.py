from django.db import models

from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page as WagtailPage
from wagtail.wagtailimages.blocks import ImageChooserBlock


class StepBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    title = blocks.TextBlock(required=False)
    text = blocks.TextBlock(required=False)


class Page(WagtailPage):
    meta_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title",icon="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock(icon="image")),
        ('step_blocks', blocks.ListBlock(StepBlock(), template='pages/blocks/projects.html', icon="image")),
    ], null=True)

    api_fields = ['title', 'meta_image', 'body', 'type']

Page.content_panels = [
    FieldPanel('title'),
    FieldPanel('meta_image'),
    StreamFieldPanel('body'),
]
