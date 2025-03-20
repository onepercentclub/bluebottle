from django.conf import settings
from django_quill.fields import QuillField
from django_quill.forms import QuillFormField
from django_quill.widgets import QuillWidget

STATIC_URL = getattr(settings, "STATIC_URL", "/static/")

MEDIA_JS = [
    f"{STATIC_URL}django_quill/highlight.min.js",
    f"{STATIC_URL}django_quill/quill.min.js",
    f"{STATIC_URL}django_quill/quill.imageCompressor.min.js",
    f"{STATIC_URL}django_quill/quill-resize-module.min.js",
    f"{STATIC_URL}django_quill/django_quill.js",
]

MEDIA_CSS = [
    f"{STATIC_URL}css/quill.snow.css",
    f"{STATIC_URL}css/darcula.min.css",
    f"{STATIC_URL}css/resize.min.css",
    f"{STATIC_URL}django_quill/django_quill.css",
]


class RichTextWidget(QuillWidget):
    class Media:
        js = MEDIA_JS
        css = {"all": MEDIA_CSS}


class RichTextFormField(QuillFormField):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            {
                "widget": RichTextWidget(),
            }
        )
        super().__init__(*args, **kwargs)


class RichTextField(QuillField):

    def formfield(self, **kwargs):
        kwargs.update({"form_class": RichTextFormField})
        return super().formfield(**kwargs)
