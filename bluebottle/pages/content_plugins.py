from bluebottle.pages.models import ImageTextItem

from fluent_contents.extensions import plugin_pool, ContentPlugin


@plugin_pool.register
class ImageTextPlugin(ContentPlugin):
    model = ImageTextItem
    render_template = "pages/plugins/imagetext/default.html"
