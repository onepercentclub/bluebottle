from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page as WagtailPage
from bluebottle.cms.blocks import (
    ProjectListBlock, ItemsBlock, ArticleBlock, StepBlock, OneSectionBlock,
    VideoBlock, SectionListBlock
)

from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailcore import blocks


class Page(WagtailPage):
    body = StreamField([
        ('article', ArticleBlock()),
        ('block_items', ItemsBlock()),
        ('projects', ProjectListBlock()),
        # For now only show main 'section' building blocks
        ('heading', blocks.CharBlock(classname="full title", icon="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock(icon="image")),
        ('step_blocks', SectionListBlock(StepBlock(), template='pages/blocks/projects.html', icon="image")),
        ('one_section', OneSectionBlock()),
        ('video', VideoBlock(icon='media')),
    ], null=True)

    api_fields = ['title', 'meta_image', 'body', 'type']

Page.content_panels = [
    FieldPanel('title'),
    StreamFieldPanel('body'),
]
