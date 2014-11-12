from django.test import TestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.wallposts import TextWallPostFactory
from bluebottle.wallposts.models import Reaction
from bluebottle.bb_follow.models import Follow
from utils.tests.utils import BookingTestCase



class FollowTests(BookingTestCase):
	""" Testcases for the creation of a Follow object """

	def setUp(self):
		self.init_projects()

		self.some_user = BlueBottleUserFactory.create()
		self.another_user = BlueBottleUserFactory.create()
		self.phase1 = ProjectPhaseFactory.create(slug='realised') # Required model for bb_payouts signals 
		self.project = ProjectFactory(owner=self.some_user, status=self.phase1)
		self.task = TaskFactory.create(
            author=self.project.owner,
            project=self.project,
        )

	def test_create_follow_wallpost_project(self):
		""" Test that a Follow object is created between the user and the project when a wallpost is created """ 
		self.assertEqual(Follow.objects.count(), 0)

		# Create a text WallPost for our dummy project
		some_wallpost = TextWallPostFactory.create(content_object=self.project, author=self.another_user)

		self.assertEqual(Follow.objects.count(), 1)
		self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
		self.assertEqual(Follow.objects.all()[0].user, self.another_user)

	def test_create_follow_reaction_project(self):
		#Reaction.objects.create(text='Hello world', wallpost=w, author=self.user_a)
		pass

	def test_create_follow_wallpost_task(self):
		pass

	def test_create_follow_reaction_task(self):
		pass

	def test_create_follow_donation(self):
		pass

	def test_no_duplicate_follow(self):
		pass

