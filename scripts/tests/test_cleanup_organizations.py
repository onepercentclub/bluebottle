import io
from contextlib import redirect_stdout

from bluebottle.activity_links.tests.factories import LinkedDeedFactory
from bluebottle.activity_pub.tests.factories import OrganizationFactory as ActorFactory
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase
from scripts.cleanup_organizations import run


class CleanupOrganizationsScriptTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        Organization.objects.all().delete()

    def run_script(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            run('tenant=test', *args)
        return output.getvalue()

    def exists(self, organization):
        return Organization.objects.filter(pk=organization.pk).exists()

    def test_dry_run_changes_nothing(self):
        unused = OrganizationFactory.create(name='Unused')
        OrganizationFactory.create(name='Twin')
        OrganizationFactory.create(name='TWIN')

        output = self.run_script()

        self.assertEqual(Organization.objects.count(), 3)
        self.assertTrue(self.exists(unused))
        self.assertIn('remove unused: Unused', output)
        self.assertIn('merge', output)
        self.assertIn("--script-args=fix", output)

    def test_removes_unused(self):
        unused = OrganizationFactory.create(name='Unused')

        self.run_script('fix')

        self.assertFalse(self.exists(unused))

    def test_keeps_used_organizations(self):
        with_activity = OrganizationFactory.create(name='With activity')
        DeedFactory.create(organization=with_activity)
        with_initiative = OrganizationFactory.create(name='With initiative')
        InitiativeFactory.create(organization=with_initiative, has_organization=True)
        with_link = OrganizationFactory.create(name='With link')
        LinkedDeedFactory.create(host_organization=with_link)
        with_hosted = OrganizationFactory.create(name='With hosted activity')
        DeedFactory.create(host_organization=with_hosted)
        with_connect = OrganizationFactory.create(name='With connect')
        ActorFactory.create(organization=with_connect)
        with_member = OrganizationFactory.create(name='With member')
        BlueBottleUserFactory.create(partner_organization=with_member)

        self.run_script('fix')

        for organization in (
            with_activity, with_initiative, with_link, with_hosted, with_connect, with_member
        ):
            self.assertTrue(self.exists(organization), organization.name)
        self.assertEqual(Member.objects.filter(partner_organization=with_member).count(), 1)

    def test_merges_same_name_case_insensitive(self):
        first = OrganizationFactory.create(name='Dharma Initiative')
        second = OrganizationFactory.create(name='dharma initiative ')
        DeedFactory.create(organization=first)
        deed = DeedFactory.create(organization=second)
        initiative = InitiativeFactory.create(organization=second, has_organization=True)
        link = LinkedDeedFactory.create(host_organization=second)

        self.run_script('fix')

        self.assertTrue(self.exists(first))
        self.assertFalse(self.exists(second))
        deed.refresh_from_db()
        initiative.refresh_from_db()
        link.refresh_from_db()
        self.assertEqual(deed.organization, first)
        self.assertEqual(initiative.organization, first)
        self.assertEqual(link.host_organization, first)

    def test_merge_keeps_the_oldest_and_repoints_everything(self):
        oldest = OrganizationFactory.create(name='Used twice')
        other = OrganizationFactory.create(name='USED TWICE')
        deeds = DeedFactory.create_batch(2, organization=other)
        DeedFactory.create(organization=oldest)
        initiative = InitiativeFactory.create(organization=other, has_organization=True)

        self.run_script('fix')

        self.assertEqual(Organization.objects.get().pk, oldest.pk)
        for deed in deeds:
            deed.refresh_from_db()
            self.assertEqual(deed.organization, oldest)
        initiative.refresh_from_db()
        self.assertEqual(initiative.organization, oldest)

    def test_merge_copies_missing_fields_and_verified(self):
        oldest = OrganizationFactory.create(name='Same', website='', verified=False)
        verified = OrganizationFactory.create(name='SAME', website='https://same.org', verified=True)
        InitiativeFactory.create(organization=oldest, has_organization=True)
        InitiativeFactory.create(organization=verified, has_organization=True)

        self.run_script('fix')

        target = Organization.objects.get()
        self.assertEqual(target.pk, oldest.pk)
        self.assertTrue(target.verified)
        self.assertEqual(target.website, 'https://same.org')
        self.assertEqual(Initiative.objects.filter(organization=target).count(), 2)

    def test_does_not_merge_two_connect_organizations(self):
        first = OrganizationFactory.create(name='Partner')
        second = OrganizationFactory.create(name='PARTNER')
        ActorFactory.create(organization=first)
        ActorFactory.create(organization=second)

        output = self.run_script('fix')

        self.assertTrue(self.exists(first))
        self.assertTrue(self.exists(second))
        self.assertIn('skip merge', output)

    def test_moves_the_actor_to_the_organization_it_is_merged_into(self):
        plain = OrganizationFactory.create(name='Partner')
        connected = OrganizationFactory.create(name='partner')
        InitiativeFactory.create(organization=plain, has_organization=True)
        actor = ActorFactory.create(organization=connected)

        self.run_script('fix')

        self.assertEqual(Organization.objects.get().pk, plain.pk)
        actor.refresh_from_db()
        self.assertEqual(actor.organization_id, plain.pk)

    def test_merges_organizations_that_only_have_an_origin(self):
        remote = ActorFactory.create(iri='https://partner.example/organization/1')
        other_remote = ActorFactory.create(iri='https://partner.example/organization/2')
        first = OrganizationFactory.create(name='Bag that Banner', origin=remote)
        second = OrganizationFactory.create(name='bag that banner', origin=other_remote)
        deed = DeedFactory.create(organization=first)

        self.run_script('fix')

        self.assertTrue(self.exists(first))
        self.assertFalse(self.exists(second))
        deed.refresh_from_db()
        self.assertEqual(deed.organization, first)

    def test_merge_moves_the_actor_and_repoints_origin_only_copies(self):
        remote = ActorFactory.create(iri='https://partner.example/organization/1')
        copy = OrganizationFactory.create(name='Bag that Banner', origin=remote)
        actor_organization = OrganizationFactory.create(name='BAG THAT BANNER')
        actor = ActorFactory.create(organization=actor_organization)
        deed = DeedFactory.create(organization=actor_organization)

        self.run_script('fix')

        self.assertTrue(self.exists(copy))
        self.assertFalse(self.exists(actor_organization))
        deed.refresh_from_db()
        self.assertEqual(deed.organization, copy)
        actor.refresh_from_db()
        self.assertEqual(actor.organization_id, copy.pk)
        copy.refresh_from_db()
        self.assertEqual(copy.origin_id, remote.pk)

    def test_args_in_one_string(self):
        unused = OrganizationFactory.create(name='Unused')

        output = io.StringIO()
        with redirect_stdout(output):
            run('fix tenant=test')

        self.assertFalse(self.exists(unused))

    def test_unknown_tenant_does_nothing(self):
        unused = OrganizationFactory.create(name='Unused')
        output = io.StringIO()
        with redirect_stdout(output):
            run('fix', 'tenant=nope')

        self.assertTrue(self.exists(unused))
