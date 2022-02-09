from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
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


class MemberSegmentTestCase(BluebottleTestCase):

    def setUp(self):
        self.segment_type = SegmentTypeFactory.create()

    def test_new_user_no_segments(self):
        SegmentFactory.create(
            segment_type=self.segment_type,
            closed=True
        )

        mart = BlueBottleUserFactory.create(
            email='mart.hoogkamer@leidse-zangers.nl'
        )
        self.assertEqual(mart.segments.first(), None)

    def test_new_user_added_to_segment(self):
        segment = SegmentFactory.create(
            segment_type=self.segment_type,
            email_domains=['leidse-zangers.nl'],
            closed=True
        )

        mart = BlueBottleUserFactory.create(
            email='mart.hoogkamer@leidse-zangers.nl'
        )
        self.assertEqual(mart.segments.first(), segment)

        jan = BlueBottleUserFactory.create(
            email='jan.keizer@paling-sound.nl'
        )
        self.assertEqual(jan.segments.first(), None)

    def test_user_added_to_segment_when_setting_email_domain(self):
        robbie = BlueBottleUserFactory.create(
            email='rubberen.robbie@leidse-zangers.nl'
        )
        jan = BlueBottleUserFactory.create(
            email='jan.keizer@paling-sound.nl'
        )
        segment = SegmentFactory.create(
            segment_type=self.segment_type,
            email_domains=['leidse-zangers.nl'],
            closed=True
        )

        self.assertEqual(robbie.segments.first(), segment)
        self.assertEqual(jan.segments.first(), None)
