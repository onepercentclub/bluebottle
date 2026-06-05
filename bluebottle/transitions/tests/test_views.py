from django.test import TestCase

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.transitions.views import TransitionList
from rest_framework_json_api.parsers import JSONParser


class TransitionListTestCase(TestCase):
    def test_uses_json_api_renderer_and_parser(self):
        self.assertIn(JSONParser, TransitionList.parser_classes)
        self.assertIn(BluebottleJSONAPIRenderer, TransitionList.renderer_classes)

    def test_has_open_permissions(self):
        self.assertEqual(TransitionList.permission_classes, ())
