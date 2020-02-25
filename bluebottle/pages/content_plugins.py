from django.utils.translation import ugettext_lazy as _

from fluent_contents.extensions import plugin_pool, ContentPlugin

from bluebottle.pages.models import ImageTextItem, DocumentItem, ActionItem, ColumnsItem, ImageTextRoundItem


@plugin_pool.register
class ImageTextPlugin(ContentPlugin):
    model = ImageTextItem
    render_template = "pages/plugins/imagetext/default.html"
    category = _("Multimedia")


@plugin_pool.register
class ImageTextRoundPlugin(ContentPlugin):
    model = ImageTextRoundItem
    render_template = "pages/plugins/imagetext/default.html"
    category = _("Multimedia")


@plugin_pool.register
class DocumentPlugin(ContentPlugin):
    model = DocumentItem
    render_template = "pages/plugins/document/default.html"
    category = _("Multimedia")


@plugin_pool.register
class ActionPlugin(ContentPlugin):
    model = ActionItem
    render_template = "pages/plugins/action/default.html"
    category = _("Multimedia")


@plugin_pool.register
class ColumnsPlugin(ContentPlugin):
    model = ColumnsItem
    render_template = "pages/plugins/columns/default.html"
    category = _("Multimedia")
