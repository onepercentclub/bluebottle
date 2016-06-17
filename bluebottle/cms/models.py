from django import forms
from django.db import models
from django.utils.functional import cached_property

from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page as WagtailPage
from wagtail.wagtailimages.blocks import ImageChooserBlock

from bluebottle.cms.blocks import ProjectChooserBlock


class StepBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    title = blocks.TextBlock(required=False)
    text = blocks.TextBlock(required=False)


class ArticleSection(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    image = ImageChooserBlock()
    text = blocks.RichTextBlock(required=False)


class ButtonBlock(blocks.StructBlock):
    title = blocks.TextBlock(required=True)
    url = blocks.TextBlock(required=True)


class BlockItemSection(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    intro = blocks.TextBlock(required=False)
    blocks = blocks.ListBlock(StepBlock(), template='pages/blocks/projects.html', icon="image")
    button = ButtonBlock(required=False)


class ProjectShowSection(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    projects = blocks.ListBlock(ProjectChooserBlock())


class Page(WagtailPage):
    body = StreamField([
        ('article', ArticleSection()),
        ('block_items', BlockItemSection()),
        ('projects', ProjectShowSection()),
        # For now only show main 'section' building blocks
        ('heading', blocks.CharBlock(classname="full title",icon="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock(icon="image")),
        ('step_blocks', blocks.ListBlock(StepBlock(), template='pages/blocks/projects.html', icon="image")),
    ], null=True)

    api_fields = ['title', 'meta_image', 'body', 'type']

Page.content_panels = [
    FieldPanel('title'),
    StreamFieldPanel('body'),
]
