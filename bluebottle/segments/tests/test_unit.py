from bluebottle.test.utils import BluebottleTestCase
from bluebottle.segments.tests.factories import SegmentTypeFactory
from bluebottle.segments.models import Segment


class TestSegmentModel(BluebottleTestCase):
    """
        save() automatically updates some fields, specifically
        the status field. Make sure it picks the right one
    """
    def setUp(self):
        self.type = SegmentTypeFactory.create()

    def test_save_add_name_to_alternate_names(self):
        segment = Segment(segment_type=self.type, name='test')
        segment.save()

        self.assertEqual(segment.alternate_names, ['test'])

    def test_save_add_name_to_alternate_names_only_once(self):
        segment = Segment(segment_type=self.type, name='test')
        segment.save()

        segment.save()

        self.assertEqual(segment.alternate_names, ['test'])

    def test_text_color(self):
        segment = Segment(
            segment_type=self.type,
            name='test',
        )

        for color, text_color in [
            ('#ffffff', 'grey'),
            ('#000000', 'white'),
            ('#ff4422', 'white')
        ]:
            segment.background_color = color
            self.assertEqual(segment.text_color, text_color)
