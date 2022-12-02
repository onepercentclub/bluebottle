from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.wallposts import (
    MediaWallpostFactory
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.wallposts.models import Wallpost
from bluebottle.wallposts.tasks import data_retention_wallposts_task


class WallpostDataRetentionTest(BluebottleTestCase):

    def setUp(self):
        super(WallpostDataRetentionTest, self).setUp()
        months_ago_12 = now() - relativedelta(months=12)
        months_ago_8 = now() - relativedelta(months=8)
        months_ago_2 = now() - relativedelta(months=2)

        wp1 = MediaWallpostFactory.create()
        wp1.created = months_ago_12
        wp1.save()
        wp2 = MediaWallpostFactory.create()
        wp2.created = months_ago_8
        wp2.save()
        wp3 = MediaWallpostFactory.create()
        wp3.created = months_ago_2
        wp3.save()
        self.task = data_retention_wallposts_task

    def test_data_retention(self):
        member_settings = MemberPlatformSettings.load()
        self.assertEqual(Wallpost.objects.count(), 3)
        self.task()
        self.assertEqual(Wallpost.objects.count(), 3)
        member_settings.retention_delete = 10
        member_settings.retention_anonymize = 6
        member_settings.save()
        self.task()
        self.assertEqual(Wallpost.objects.count(), 2)
        self.assertEqual(Wallpost.objects.filter(author__isnull=False).count(), 1)
