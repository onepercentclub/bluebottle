import json

from django.test import SimpleTestCase
from django_quill.widgets import QuillWidget

from bluebottle.utils.forms import CustomMessageFormField


class CustomMessageFormFieldTestCase(SimpleTestCase):

    def test_uses_limited_quill_toolbar_config(self):
        field = CustomMessageFormField(required=False)
        self.assertIsInstance(field.widget, QuillWidget)
        self.assertEqual(field.widget.config['modules']['toolbar'], [
            ['bold', 'italic'],
            [{'list': 'ordered'}, {'list': 'bullet'}],
        ])

    def test_clean_returns_sanitized_html_from_quill_json(self):
        field = CustomMessageFormField(required=False)
        quill_value = json.dumps({
            'delta': '',
            'html': '<p>Hello <strong>world</strong></p><script>alert(1)</script>',
        })
        cleaned = field.clean(quill_value)
        self.assertEqual(cleaned, '<p>Hello <strong>world</strong></p>')

    def test_clean_converts_plain_text_to_html(self):
        field = CustomMessageFormField(required=False)
        cleaned = field.clean('Line one\n\nLine two')
        self.assertIn('<p>Line one</p>', cleaned)
        self.assertIn('Line two', cleaned)
