from django_quill.widgets import QuillWidget
from django.templatetags.static import static


MEDIA_JS = [
    static('django_quill/highlight.min.js'),
    static('django_quill/quill.min.js'),
    static('django_quill/quill.imageCompressor.min.js'),
    static('django_quill/quill-resize-module.min.js'),
    static('django_quill/django_quill.js'),
]
MEDIA_CSS = [
    static('django_quill/quill.snow.css'),
    static('django_quill/darcula.min.css'),
    static('django_quill/resize.min.css'),
    static('django_quill/django_quill.css'),
]


QuillWidget.Media.js = MEDIA_JS
QuillWidget.Media.css['all'] = MEDIA_CSS

# Patch QuillWidget.render to add custom context
# QuillWidget doesn't use get_context, it overrides render directly
original_render = QuillWidget.render


def custom_render(self, name, value, attrs=None, renderer=None):
    from django.forms.renderers import get_default_renderer
    from django.forms.utils import flatatt
    from django.utils.safestring import mark_safe
    from django_quill.widgets import json_encode
    
    # Import here to avoid circular imports
    from bluebottle.cms.models import SitePlatformSettings
    
    if renderer is None:
        renderer = get_default_renderer()
    if value is None:
        value = ""

    attrs = attrs or {}
    attrs["name"] = name
    if hasattr(value, "quill"):
        attrs["quill"] = value.quill
    else:
        attrs["value"] = value
    final_attrs = self.build_attrs(self.attrs, attrs)
    
    # Add custom context with site settings colors
    site_settings = SitePlatformSettings.load()
    
    context = {
        "final_attrs": flatatt(final_attrs),
        "id": final_attrs["id"],
        "name": final_attrs["name"],
        "config": json_encode(self.config),
        "quill": final_attrs.get("quill", None),
        "value": final_attrs.get("value", None),
        # Add custom color settings
        "action_color": site_settings.action_color,
        "action_text_color": site_settings.action_text_color,
        "description_color": site_settings.description_color,
        "description_text_color": site_settings.description_text_color,
        "link_color": site_settings.link_color,
    }
    
    return mark_safe(
        renderer.render(
            "django_quill/widget.html",
            context,
        )
    )


QuillWidget.render = custom_render
