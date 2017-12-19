from bluebottle.members.models import CustomMemberField, CustomMemberFieldSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class TestMemberPlatformSettings(BluebottleTestCase):

    def test_extra_member_fields(self):
        member = BlueBottleUserFactory.create()
        custom = CustomMemberFieldSettings.objects.create(name='Extra Info')

        # Check that the slug is set correctly
        self.assertEqual(custom.slug, 'extra-info')

        # Check that the project doesn't have extra field yet
        member.refresh_from_db()
        self.assertEqual(member.extra.count(), 0)

        CustomMemberField.objects.create(member=member, value='This is nice!', field=custom)

        # And now it should be there
        member.refresh_from_db()
        self.assertEqual(member.extra.count(), 1)
