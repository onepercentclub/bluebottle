from unittest import mock

from django.test import TestCase

from bluebottle.activity_pub.renderers import JSONLDRenderer


class JSONLDRendererTestCase(TestCase):
    def test_render_returns_json_ld_bytes(self):
        renderer = JSONLDRenderer()
        data = {
            'type': 'Note',
            'content': 'Hello',
        }
        compacted = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'Note',
            'content': 'Hello',
        }

        with mock.patch(
            'bluebottle.activity_pub.renderers.processor.compact',
            return_value=compacted,
        ):
            result = renderer.render(data)

        self.assertIn(b'Note', result)
        self.assertIn(b'Hello', result)
