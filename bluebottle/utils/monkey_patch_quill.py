from django_quill.widgets import QuillWidget
from django.templatetags.static import static


MEDIA_JS = [
    # syntax-highlight
    static('django_quill/highlight.min.js'),
    static('django_quill/quill.min.js'),
    static('django_quill/quill.imageCompressor.min.js'),
    static('django_quill/quill-resize-module.min.js'),
    static('django_quill/django_quill.js'),
    static('django_quill/highlight.min.js'),
]
MEDIA_CSS = [
    # syntax-highlight

    static('django_quill/quill.snow.css'),
    static('django_quill/darcula.min.css'),
    static('django_quill/resize.min.css'),
    static('django_quill/django_quill.css'),
]


QuillWidget.Media.js = MEDIA_JS
QuillWidget.Media.css['all'] = MEDIA_CSS
