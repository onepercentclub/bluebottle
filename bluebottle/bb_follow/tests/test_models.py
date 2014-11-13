from django.test import TestCase
from django.core import mail
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.wallposts import TextWallPostFactory
from bluebottle.wallposts.models import Reaction
from bluebottle.bb_follow.models import Follow
from bluebottle.utils.model_dispatcher import get_model_class
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.utils.utils import StatusDefinition
from utils.tests.utils import BookingTestCase


DONATION_MODEL = get_model_class("DONATIONS_DONATION_MODEL")


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
		""" Test that a Follow object is created when a user leaves a reaction on a project page"""
		self.assertEqual(Follow.objects.count(), 0)
		commenter = BlueBottleUserFactory.create()

		# Create a text WallPost for our dummy project
		some_wallpost = TextWallPostFactory.create(content_object=self.project, author=self.another_user)
		self.assertEqual(Follow.objects.count(), 1) #Side-effectg of creating the wallpost

		some_reaction = Reaction.objects.create(wallpost=some_wallpost, author=commenter, text="bla")

		self.assertEqual(Follow.objects.count(), 2)
		# Make sure to inspect the second Follow object, this is the Follow object for the Reaction
		self.assertEqual(Follow.objects.all()[1].followed_object, self.project)
		self.assertEqual(Follow.objects.all()[1].user, commenter)

	def test_create_follow_wallpost_task(self):
		""" Test that a Follow object is created when a user leaves a wallpost on a task """
		self.assertEqual(Follow.objects.count(), 0)

		# Create a text WallPost for our dummy project
		some_wallpost = TextWallPostFactory.create(content_object=self.task, author=self.another_user)

		self.assertEqual(Follow.objects.count(), 1)
		self.assertEqual(Follow.objects.all()[0].followed_object, self.task)
		self.assertEqual(Follow.objects.all()[0].user, self.another_user)

	def test_create_follow_reaction_task(self):
		""" Test that a Follow object is created when a user leaves a reaction on a task page """
		self.assertEqual(Follow.objects.count(), 0)
		commenter = BlueBottleUserFactory.create()

		# Create a text WallPost for our dummy project
		some_wallpost = TextWallPostFactory.create(content_object=self.task, author=self.another_user)
		self.assertEqual(Follow.objects.count(), 1) #Side-effectg of creating the wallpost

		some_reaction = Reaction.objects.create(wallpost=some_wallpost, author=commenter, text="bla")

		self.assertEqual(Follow.objects.count(), 2)
		# Make sure to inspect the second Follow object, this is the Follow object for the Reaction
		self.assertEqual(Follow.objects.all()[1].followed_object, self.task)
		self.assertEqual(Follow.objects.all()[1].user, commenter)

	def test_create_follow_donation(self):
		""" Test that a Follow object is created if a user does a donation to a project """
		self.assertEqual(Follow.objects.count(), 0)

		order = OrderFactory.create(user=self.another_user, status=StatusDefinition.CREATED)
		donation = DonationFactory(order=order, amount=35, project=self.project)

		self.assertEqual(Follow.objects.count(), 1)
		self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
		self.assertEqual(Follow.objects.all()[0].user, self.another_user)

	def test_no_duplicate_follow(self):
		""" Test that no duplicate followers are created """
		self.assertEqual(Follow.objects.count(), 0)
		commenter = BlueBottleUserFactory.create()

		# Create a text WallPost for our dummy project
		some_wallpost = TextWallPostFactory.create(content_object=self.project, author=self.another_user, text="test1")
		self.assertEqual(Follow.objects.count(), 1) #Side-effectg of creating the wallpost

		some_reaction = Reaction.objects.create(wallpost=some_wallpost, author=commenter, text="bla")
		some_reaction_2 = Reaction.objects.create(wallpost=some_wallpost, author=commenter, text="bla2")

		self.assertEqual(Follow.objects.count(), 2)
		# Make sure to inspect the second Follow object, this is the Follow object for the Reaction
		self.assertEqual(Follow.objects.all()[1].followed_object, self.project)
		self.assertEqual(Follow.objects.all()[1].user, commenter)

	def test_not_follow_own_project(self):
		""" Test that users do not follow their own project page """
		self.assertEqual(Follow.objects.count(), 0)

		some_wallpost = TextWallPostFactory.create(content_object=self.project, author=self.some_user, text="test1")

		self.assertEqual(Follow.objects.count(), 0)


	def test_not_follow_own_task(self):
		""" Test that users do not follow their own task page """
		self.assertEqual(Follow.objects.count(), 0)

		some_wallpost = TextWallPostFactory.create(content_object=self.task, author=self.some_user, text="test1")

		self.assertEqual(Follow.objects.count(), 0)


	def test_not_follow_own_donation_project(self):
		""" Test that a user making a donation to its own project does not become a follower """
		self.assertEqual(Follow.objects.count(), 0)

		order = OrderFactory.create(user=self.some_user, status=StatusDefinition.CREATED)
		donation = DonationFactory(order=order, amount=35, project=self.project)

		self.assertEqual(Follow.objects.count(), 0)

	def test_wallpost_no_mail(self):
		""" Test that followers don't get an email if email_followers is false. Email_followers boolean is false by default on wallpost model"""
		self.assertEqual(len(mail.outbox), 0)
		self.assertEqual(Follow.objects.count(), 0)
		commenter = BlueBottleUserFactory.create()
		commenter2 = BlueBottleUserFactory.create()

		# Create a text WallPost for our dummy project
		some_wallpost = TextWallPostFactory.create(content_object=self.project, author=self.another_user, text="test1")
		some_reaction = Reaction.objects.create(wallpost=some_wallpost, author=commenter, text="bla")
		some_reaction_2 = Reaction.objects.create(wallpost=some_wallpost, author=commenter2, text="bla2")

		self.assertEqual(Follow.objects.count(), 3)
		# Some other emails are sent, so we do not compare the mail count. Instead we look at the subject
		for email in mail.outbox:
			self.assertTrue("Mail with the wallpost" not in email.subject)

	def test_wallpost_mail(self):
		""" Test that followers get an email when the email_followers option is selected """
		self.assertEqual(len(mail.outbox), 0)
		self.assertEqual(Follow.objects.count(), 0)
		commenter = BlueBottleUserFactory.create()
		commenter2 = BlueBottleUserFactory.create()

		# This creates a follower but doesn't send emails to them
		some_wallpost = TextWallPostFactory.create(content_object=self.project, author=self.another_user, text="test1", email_followers=False)
		# We create three followers.
		some_reaction = Reaction.objects.create(wallpost=some_wallpost, author=commenter, text="bla")
		some_reaction_2 = Reaction.objects.create(wallpost=some_wallpost, author=commenter2, text="bla2")
		some_wallpost2 = TextWallPostFactory.create(content_object=self.project, author=self.another_user, text="test1", email_followers=True)

		self.assertEqual(Follow.objects.count(), 3)
		mail_count = 0

		for email in mail.outbox:
			if "Mail with the wallpost" in email.subject:
				mail_count += 1
				self.assertTrue(email.to[0] in [commenter.email, commenter2.email, self.another_user.email])
		self.assertEqual(mail_count, Follow.objects.count())

		

