from django.test import TestCase

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer


class BluebottleJSONAPIRendererTestCase(TestCase):
    def test_indent_is_four_spaces(self):
        renderer = BluebottleJSONAPIRenderer()
        self.assertEqual(renderer.get_indent(), 4)
