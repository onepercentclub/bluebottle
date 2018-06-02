from django.contrib.admin.sites import AdminSite

from bluebottle.bb_follow.admin import FollowAdmin
from bluebottle.bb_follow.models import Follow
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.follow import FollowFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class FollowAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super(FollowAdminTest, self).setUp()
        self.site = AdminSite()
        self.init_projects()
        self.follow_admin = FollowAdmin(Follow, self.site)

    def test_follow_object_title(self):
        project = ProjectFactory.create()
        follow = FollowFactory.create(followed_object=project)
        title = self.follow_admin.title(follow)
        self.assertEqual(project.title, title)

    def test_follow_object_without_title(self):
        user = BlueBottleUserFactory.create()
        follow = FollowFactory.create(followed_object=user)
        title = self.follow_admin.title(follow)
        self.assertEqual(title, '-')

    def test_follow_without_object(self):
        project = ProjectFactory.create()
        follow = FollowFactory.create(followed_object=project)
        project.delete()
        title = self.follow_admin.title(follow)
        self.assertEqual(title, '-')
