from wagtail.wagtailcore.blocks import ChooserBlock

from wagtail.wagtailcore import blocks
from bluebottle.projects.models import Project

from wagtail.wagtailimages.blocks import ImageChooserBlock
from bluebottle.cms.widgets import AdminProjectChooser


class StepBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    title = blocks.TextBlock(required=False)
    text = blocks.TextBlock(required=False)


class ArticleBlock(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    image = ImageChooserBlock()
    text = blocks.RichTextBlock(required=False)


class ButtonBlock(blocks.StructBlock):
    title = blocks.TextBlock(required=True)
    url = blocks.TextBlock(required=True)


class OneSectionBlock(StepBlock):
    action = ButtonBlock(required=False)


class VideoBlock(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    url = blocks.URLBlock(required=False)
    background_image = ImageChooserBlock()
    button_text = blocks.TextBlock(required=False)


class ProjectChooserBlock(ChooserBlock):
    target_model = Project

    widget = AdminProjectChooser

    def render_basic(self, value):
        return value.title

    class Meta:
        icon = "image"


class ItemsBlock(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    intro = blocks.TextBlock(required=False)
    blocks = blocks.ListBlock(StepBlock(), template='pages/blocks/projects.html', icon="image")
    button = ButtonBlock(required=False)


class ProjectListBlock(blocks.StructBlock):
    title = blocks.TextBlock(required=False)
    projects = blocks.ListBlock(ProjectChooserBlock())
