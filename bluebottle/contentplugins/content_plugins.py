"""
ContentItem plugin definitions for django-fluent-contents
"""
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from fluent_contents.extensions import plugin_pool, ContentPlugin

from .models import PictureItem


@plugin_pool.register
class PicturePlugin(ContentPlugin):
    """
    Plugin for pictures in the blog/news content.
    """
    model = PictureItem
    category = _("Multimedia")
    render_template = 'contentplugins/picture.html'

    fieldsets = (
        (None, {'fields': ('image', )}),
    )

    radio_fields = {
        'align': admin.HORIZONTAL
    }
