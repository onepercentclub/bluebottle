import json

from django.test import SimpleTestCase
from django_quill.quill import Quill

from bluebottle.utils.forms import CustomMessageFormField, html_to_quill_json


class CustomMessageFormFieldTestCase(SimpleTestCase):

    def test_html_to_quill_json_wraps_html(self):
        value = html_to_quill_json('<p>Hello <strong>world</strong></p>')
        quill = Quill(value)
        self.assertIn('<strong>world</strong>', quill.html)

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
