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


class MemberSegmentTestCase(BluebottleTestCase):

    def setUp(self):
        self.segment_type = SegmentTypeFactory.create()

    def test_new_user_added_to_segment(self):
        segment = SegmentFactory.create(
            segment_type=self.segment_type,
            email_domain='leidse-zangers.nl',
            closed=True
        )

        mart = BlueBottleUserFactory.create(
            email='mart.hoogkamer@leidse-zangers.nl'
        )
        self.assertTrue(segment in mart.segments.all())

        jan = BlueBottleUserFactory.create(
            email='jan.keizer@paling-sound.nl'
        )
        self.assertFalse(segment in jan.segments.all())
