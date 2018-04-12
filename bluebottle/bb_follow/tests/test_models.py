from bluebottle.test.utils import BluebottleTestCase
from django.core import mail
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, \
    ProjectPhaseFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.wallposts import TextWallpostFactory
from bluebottle.bb_follow.models import Follow
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.utils.utils import StatusDefinition


class FollowTests(BluebottleTestCase):
    """ Testcases for the creation of a Follow object """

    def setUp(self):
        super(FollowTests, self).setUp()
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()
        self.phase1 = ProjectPhaseFactory.create(
            slug='realised')  # Required model for bb_payouts signals
        self.project = ProjectFactory(owner=self.some_user, status=self.phase1)

        self.task = TaskFactory.create(
            author=self.project.owner,
            project=self.project,
        )

    def test_create_follow_donation(self):
        """ Test that a Follow object is created if a user does a donation to a project """
        self.assertEqual(Follow.objects.count(), 0)

        order = OrderFactory.create(user=self.another_user,
                                    status=StatusDefinition.CREATED)
        # Make sure to set Fundraiser to None. Otherwise, a fundraiser is created
        DonationFactory(order=order, amount=35,
                        project=self.project,
                        fundraiser=None)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
        self.assertEqual(Follow.objects.all()[0].user, self.another_user)

    def test_create_follow_create_task(self):
        """ Test that a Follow is created if a user, that is not the owner, creates a task. User will follow project """
        self.assertEqual(Follow.objects.count(), 0)

        task_owner = BlueBottleUserFactory.create()

        TaskFactory.create(
            author=task_owner,
            project=self.project,
        )

        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
        self.assertEqual(Follow.objects.all()[0].user, task_owner)

        # Test that no follower is created when the task owner is also the project owner
        TaskFactory.create(
            author=self.project.owner,
            project=self.project
        )

        self.assertEqual(Follow.objects.count(), 1)

    def test_create_follow_create_vote(self):
        """
            Test that a Follow is created if a user, that is not the owner,
            casts a vote. User will follow project.
        """
        self.assertEqual(Follow.objects.count(), 0)

        voter = BlueBottleUserFactory.create()

        VoteFactory.create(
            voter=voter,
            project=self.project,
        )

        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
        self.assertEqual(Follow.objects.all()[0].user, voter)

        # Test that no follower is created when the task owner
        # is also the project owner
        VoteFactory.create(
            voter=self.project.owner,
            project=self.project
        )

        self.assertEqual(Follow.objects.count(), 1)

    def test_create_follow_create_taskmember(self):
        """
            Test that a Follow object is created when a task member is
            created. User will follow Task, not the project
            """
        self.assertEqual(Follow.objects.count(), 0)

        task_member_1 = TaskMemberFactory(task=self.task)
        self.assertEqual(Follow.objects.count(), 2)
        self.assertEqual(Follow.objects.all()[0].followed_object, self.task)
        self.assertEqual(Follow.objects.all()[0].user, task_member_1.member)

        self.assertEqual(Follow.objects.all()[1].followed_object, self.task.project)
        self.assertEqual(Follow.objects.all()[1].user, task_member_1.member)

    def test_create_follow_create_fundraiser(self):
        """ Test that a Fundraiser also becomes a follower of a project """
        self.assertEqual(Follow.objects.count(), 0)

        fundraiser_person = BlueBottleUserFactory.create()
        FundraiserFactory(project=self.project, owner=fundraiser_person)

        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
        self.assertEqual(Follow.objects.all()[0].user, fundraiser_person)

    def test_no_duplicate_follow(self):
        """ Test that no duplicate followers are created """
        self.assertEqual(Follow.objects.count(), 0)
        user = BlueBottleUserFactory.create()

        order = OrderFactory.create(user=user, status=StatusDefinition.CREATED)
        # Make sure to set Fundraiser to None. Otherwise, fundraiser is created
        DonationFactory(order=order, amount=35,
                        project=self.project, fundraiser=None)

        order = OrderFactory.create(user=user, status=StatusDefinition.CREATED)
        # Make sure to set Fundraiser to None. Otherwise, fundraiser is created
        DonationFactory(order=order, amount=35,
                        project=self.project, fundraiser=None)

        self.assertEqual(Follow.objects.count(), 1)
        # Make sure to inspect the second Follow object, this is the Follow
        # object for the donation
        self.assertEqual(Follow.objects.all()[0].followed_object, self.project)
        self.assertEqual(Follow.objects.all()[0].user, user)

    def test_not_follow_own_project(self):
        """ Test that users do not follow their own project page """
        self.assertEqual(Follow.objects.count(), 0)

        TextWallpostFactory.create(content_object=self.project,
                                   author=self.some_user,
                                   text="test1")

        self.assertEqual(Follow.objects.count(), 0)

    def test_not_follow_own_task(self):
        """ Test that users do not follow their own task page """
        self.assertEqual(Follow.objects.count(), 0)

        TextWallpostFactory.create(content_object=self.task,
                                   author=self.some_user,
                                   text="test1")

        self.assertEqual(Follow.objects.count(), 0)

    def test_not_follow_own_donation_project(self):
        """ Test that a user making a donation to its own project does not become a follower """
        self.assertEqual(Follow.objects.count(), 0)

        order = OrderFactory.create(user=self.some_user,
                                    status=StatusDefinition.CREATED)
        # Make sure that no fundraisers are created. A new fundraiser will also create a follower
        DonationFactory(order=order, amount=35,
                        project=self.project, fundraiser=None)

        self.assertEqual(Follow.objects.count(), 0)

    def test_wallpost_no_mail(self):
        """ Test that followers don't get an email if email_followers is false.
            Email_followers boolean is false by default on wallpost model"""
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Follow.objects.count(), 0)
        BlueBottleUserFactory.create()
        BlueBottleUserFactory.create()

        # Create follower by creating a donation

        order = OrderFactory.create(user=self.another_user,
                                    status=StatusDefinition.CREATED)
        # Make sure to set Fundraiser to None. Otherwise, a fundraiser is created
        DonationFactory(order=order, amount=35,
                        project=self.project, fundraiser=None)

        # Create follower by creating a task owner

        task_owner1 = BlueBottleUserFactory.create()

        TaskFactory.create(
            author=task_owner1,
            project=self.project
        )

        # Verify we have two followers
        self.assertEqual(Follow.objects.count(), 2)

        # Create a text Wallpost for our dummy project
        TextWallpostFactory.create(content_object=self.project,
                                   author=self.project.owner,
                                   text="test1",
                                   email_followers=False)

        self.assertEqual(Follow.objects.count(), 2)

        # Some other emails are sent, so we do not compare the mail count. Instead we look at the subject
        for email in mail.outbox:
            self.assertTrue("New wallpost on" not in email.subject)

    def test_wallpost_mail_project(self):
        """
        Test that the relevant people get an email when the
        email_followers option is selected for a project
        """

        # On a project page, task owners, fundraisers, and people who donated,  get a mail.

        # Create a follower by being a task owner
        task_owner1 = BlueBottleUserFactory.create()

        TaskFactory.create(
            author=task_owner1,
            project=self.project
        )

        # Add extra project and owner that should not get any email
        project_owner = BlueBottleUserFactory.create()
        ProjectFactory(owner=project_owner, status=self.phase1)

        # iLeaving a wallpost should not create a follower
        commenter = BlueBottleUserFactory.create()
        TextWallpostFactory.create(content_object=self.project,
                                   author=commenter,
                                   text="test1",
                                   email_followers=False)

        # Create a follower by donating
        donator1 = BlueBottleUserFactory.create()
        order = OrderFactory.create(user=donator1,
                                    status=StatusDefinition.CREATED)
        DonationFactory(order=order, amount=35,
                        project=self.project,
                        fundraiser=None)

        # Create a follower by being a fundraiser for the project
        fundraiser_person = BlueBottleUserFactory.create()
        FundraiserFactory(project=self.project, owner=fundraiser_person)

        self.assertEqual(Follow.objects.count(), 3)

        voter = BlueBottleUserFactory.create()
        VoteFactory(voter=voter, project=self.project)

        self.assertEqual(Follow.objects.count(), 4)

        # Project owner creates a wallpost and emails followers
        TextWallpostFactory.create(
            content_object=self.project, author=self.project.owner,
            text="test2", email_followers=True)

        mail_count = 0

        # People who should get an email: self.some_user, voter, task_owner1,
        # fundraiser_person, commenter, and donator1
        receivers = [voter.email, task_owner1.email, fundraiser_person.email, donator1.email]
        for email in mail.outbox:
            if "New wallpost on" in email.subject:
                mail_count += 1
                self.assertTrue(email.to[0] in receivers)
                receivers.remove(email.to[0])
        self.assertEqual(mail_count, 4)
        self.assertEqual(receivers, [])

    def test_wallpost_mail_task(self):
        """ Test that the relevant people get an email when the email_followers option is selected for a task """

        # On a task page, the task members, task owners, get an email --> Followers

        project_owner = BlueBottleUserFactory.create()
        project2 = ProjectFactory(owner=project_owner, status=self.phase1)

        task_owner1 = BlueBottleUserFactory.create()

        task = TaskFactory.create(
            author=task_owner1,
            project=project2
        )

        task_member_1 = TaskMemberFactory(task=task)
        task_member_2 = TaskMemberFactory(task=task)

        mail.outbox = []

        self.assertEqual(Follow.objects.count(), 5)
        for follower in Follow.objects.all():
            if follower.user != task_owner1:
                self.assertTrue(follower.followed_object in (task, task.project))

        TextWallpostFactory.create(content_object=task,
                                   author=task_owner1,
                                   text="test2",
                                   email_followers=True)

        mail_count = 0

        receivers = [task_member_1.member.email, task_member_2.member.email]

        for email in mail.outbox:
            if "New wallpost on" in email.subject:
                mail_count += 1
                self.assertTrue(email.to[0] in receivers)
                receivers.remove(email.to[0])

        self.assertEqual(mail_count, 2)
        self.assertEqual(receivers, [])

    def test_wallpost_mail_fundraiser(self):
        """ Test that the relevant people get an email when the email_followers option is selected for a fundraiser """

        # On a Fundraiser page, people who posted to the wall and who donated get an email --> Followers
        self.assertEqual(Follow.objects.count(), 0)

        # A user creates a fundraiser
        fundraiser_person = BlueBottleUserFactory.create()
        fundraiser = FundraiserFactory(project=self.project,
                                       owner=fundraiser_person)

        # Two people donate to the fundraiser
        donator1 = BlueBottleUserFactory.create()
        order = OrderFactory.create(user=donator1,
                                    status=StatusDefinition.CREATED)
        DonationFactory(order=order, amount=35,
                        project=self.project,
                        fundraiser=fundraiser)

        donator2 = BlueBottleUserFactory.create()
        order2 = OrderFactory.create(user=donator2,
                                     status=StatusDefinition.CREATED)
        DonationFactory(order=order2, amount=35,
                        project=self.project,
                        fundraiser=fundraiser)

        # The fundraiser owner creates a wallpost to followers
        TextWallpostFactory.create(content_object=fundraiser,
                                   author=fundraiser_person,
                                   text="test_fundraiser",
                                   email_followers=True)

        mail_count = 0
        self.assertEqual(Follow.objects.count(), 3)

        # When the fundraiser sends an email to the followers he doesn't get one himself
        receivers = [donator1.email, donator2.email]

        for email in mail.outbox:
            if "New wallpost on" in email.subject:
                mail_count += 1
                self.assertTrue(email.to[0] in receivers)
                receivers.remove(email.to[0])

        self.assertEqual(mail_count, 2)
        self.assertEqual(receivers, [])

    def test_no_mail_no_campaign_notifications(self):
        """ Test that users who have campaign_notifications turned off don't get email """
        task_owner1 = BlueBottleUserFactory.create(campaign_notifications=False)

        TaskFactory.create(
            author=task_owner1,
            project=self.project
        )

        # Add extra project and owner that should not get any email
        project_owner = BlueBottleUserFactory.create(campaign_notifications=False)
        ProjectFactory(owner=project_owner, status=self.phase1)

        # Create a follower by donating
        donator1 = BlueBottleUserFactory.create(campaign_notifications=False)
        order = OrderFactory.create(user=donator1,
                                    status=StatusDefinition.CREATED)
        DonationFactory(order=order, amount=35,
                        project=self.project,
                        fundraiser=None)

        # Create a follower by being a fundraiser for the project
        fundraiser_person = BlueBottleUserFactory.create(campaign_notifications=False)
        FundraiserFactory(project=self.project,
                          owner=fundraiser_person)

        self.assertEqual(Follow.objects.count(), 3)

        # Create follower by voting
        voter_person = BlueBottleUserFactory.create(
            campaign_notifications=False)
        VoteFactory(voter=voter_person, project=self.project)

        # Project owner creates a wallpost and emails followers
        TextWallpostFactory.create(
            content_object=self.project, author=self.project.owner,
            text="test2", email_followers=True)

        mail_count = 0

        # People who should get an email: self.some_user, task_owner1,
        # fundraiser_person, commenter, voter and donator1
        for email in mail.outbox:
            if "New wallpost on" in email.subject:
                mail_count += 1
        self.assertEqual(mail_count, 0)

    def test_wallpost_delete_mail_project(self):
        """
        Test that the relevant people don't get an email when the
        email_followers option is selected for a project
        during wallpost create but is then deleted.
        """

        # On a project page, task owners, fundraisers, and people who donated,  get a mail.

        # Create a follower by being a task owner
        task_owner1 = BlueBottleUserFactory.create()

        TaskFactory.create(
            author=task_owner1,
            project=self.project
        )

        # Add extra project and owner that should not get any email
        project_owner = BlueBottleUserFactory.create()
        ProjectFactory(owner=project_owner, status=self.phase1)

        # iLeaving a wallpost should not create a follower
        commenter = BlueBottleUserFactory.create()
        TextWallpostFactory.create(content_object=self.project,
                                   author=commenter,
                                   text="test1",
                                   email_followers=False)

        # Create a follower by donating
        donator1 = BlueBottleUserFactory.create()
        order = OrderFactory.create(user=donator1,
                                    status=StatusDefinition.CREATED)
        DonationFactory(order=order, amount=35,
                        project=self.project,
                        fundraiser=None)

        # Create a follower by being a fundraiser for the project
        fundraiser_person = BlueBottleUserFactory.create()
        FundraiserFactory(project=self.project,
                          owner=fundraiser_person)

        self.assertEqual(Follow.objects.count(), 3)

        voter = BlueBottleUserFactory.create()
        VoteFactory(voter=voter, project=self.project)

        self.assertEqual(Follow.objects.count(), 4)

        # Project owner creates a wallpost and emails followers
        some_wallpost_2 = TextWallpostFactory.create(
            content_object=self.project, author=self.project.owner,
            text="test2", email_followers=True)

        mail_count = 0

        # People who should get an email: self.some_user, voter, task_owner1,
        # fundraiser_person, commenter, and donator1
        receivers = [voter.email, task_owner1.email,
                     fundraiser_person.email, donator1.email]
        for email in mail.outbox:
            if "New wallpost on" in email.subject:
                mail_count += 1
                self.assertTrue(email.to[0] in receivers)
                receivers.remove(email.to[0])
        self.assertEqual(mail_count, 4)
        self.assertEqual(receivers, [])

        # Setup for mail counting after wallpost delete
        mail_count = 0
        receivers = [voter.email, task_owner1.email,
                     fundraiser_person.email, donator1.email]

        # This time we can safely reset the email box to 0
        mail.outbox = []

        # Ember triggers a save to the record before the actual delete
        # therefore we can't use the Django delete function. This won't
        # trigger the email_follower signal to be fired again. To replicate
        # the server behavior we can simply re-save the wallpost record. This
        # will cause the signal to fire but with the "created" flag to False.
        some_wallpost_2.save()

        # Check that no emails about a new wallpost go out
        for email in mail.outbox:
            if "New wallpost on" in email.subject:
                mail_count += 1
                self.assertTrue(email.to[0] in receivers)
        self.assertEqual(mail_count, 0)
