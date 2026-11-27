from django.core import mail
from django.urls import reverse

from bluebottle.organizations.models import OrganizationMember
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory, OrganizationMemberFactory
)
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase


class OrganizationMemberMessageTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.organization = OrganizationFactory.create(name='Dharma')
        self.other = OrganizationFactory.create(name='Karma')
        self.member = BlueBottleUserFactory.create()
        mail.outbox = []

    def create(self, **kwargs):
        with self.captureOnCommitCallbacks(execute=True):
            return OrganizationMemberFactory.create(
                member=self.member, organization=self.organization, **kwargs
            )

    def test_added(self):
        self.create()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.member.email])
        self.assertEqual(message.subject, "You've been added to Dharma")
        self.assertIn(f'/organizations/{self.organization.pk}/', message.alternatives[0][0])

    def test_removed(self):
        membership = self.create()
        mail.outbox = []

        with self.captureOnCommitCallbacks(execute=True):
            membership.delete()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.member.email])
        self.assertEqual(message.subject, "You've been removed from Dharma")
        self.assertNotIn('/organizations/', message.alternatives[0][0])

    def test_bulk_delete(self):
        self.create()
        mail.outbox = []

        with self.captureOnCommitCallbacks(execute=True):
            OrganizationMember.objects.all().delete()

        self.assertEqual(len(mail.outbox), 1)

    def test_change_role(self):
        membership = self.create()
        mail.outbox = []

        with self.captureOnCommitCallbacks(execute=True):
            membership.role = OrganizationMember.Roles.manager
            membership.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_move(self):
        membership = self.create()
        mail.outbox = []

        with self.captureOnCommitCallbacks(execute=True):
            membership.organization = self.other
            membership.save()

        self.assertEqual(
            sorted(message.subject for message in mail.outbox),
            ["You've been added to Karma", "You've been removed from Dharma"]
        )
        self.assertEqual({message.to[0] for message in mail.outbox}, {self.member.email})

    def test_delete_member(self):
        self.create()
        mail.outbox = []

        with self.captureOnCommitCallbacks(execute=True):
            self.member.delete()

        self.assertEqual(len(mail.outbox), 0)

    def test_delete_organization(self):
        self.create()
        mail.outbox = []

        with self.captureOnCommitCallbacks(execute=True):
            self.organization.delete()

        self.assertEqual(len(mail.outbox), 0)

    def test_not_sent_before_commit(self):
        OrganizationMemberFactory.create(member=self.member, organization=self.organization)

        self.assertEqual(len(mail.outbox), 0)


class OrganizationMemberAdminMessageTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.organization = OrganizationFactory.create(name='Dharma')
        self.other = OrganizationFactory.create(name='Karma')
        self.member = BlueBottleUserFactory.create()

    def test_add_in_organization_admin(self):
        mail.outbox = []
        url = reverse('admin:organizations_organization_change', args=(self.organization.pk,))
        form = self.app.get(url).forms['organization_form']
        self.admin_add_inline_form_entry(form, 'members')
        form['members-0-member'] = self.member.pk
        form['members-0-role'] = OrganizationMember.Roles.member

        with self.captureOnCommitCallbacks(execute=True):
            form.submit().follow()

        self.assertEqual(
            [message.subject for message in mail.outbox],
            ["You've been added to Dharma"]
        )

    def test_remove_in_organization_admin(self):
        OrganizationMemberFactory.create(member=self.member, organization=self.organization)
        mail.outbox = []
        url = reverse('admin:organizations_organization_change', args=(self.organization.pk,))
        form = self.app.get(url).forms['organization_form']
        form['members-0-DELETE'] = True

        with self.captureOnCommitCallbacks(execute=True):
            form.submit().follow()

        self.assertEqual(
            [message.subject for message in mail.outbox],
            ["You've been removed from Dharma"]
        )

    def test_move_in_member_admin(self):
        OrganizationMemberFactory.create(member=self.member, organization=self.organization)
        mail.outbox = []
        url = reverse('admin:members_member_change', args=(self.member.pk,))
        form = self.app.get(url).forms['member_form']
        form['organization_memberships-0-organization'] = self.other.pk

        with self.captureOnCommitCallbacks(execute=True):
            form.submit().follow()

        self.assertEqual(
            sorted(message.subject for message in mail.outbox),
            ["You've been added to Karma", "You've been removed from Dharma"]
        )
