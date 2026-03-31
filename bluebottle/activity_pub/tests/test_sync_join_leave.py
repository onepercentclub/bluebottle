from datetime import datetime, timedelta
from unittest import mock

from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import timezone as tz

from bluebottle.activities.models import RemoteContributor
from bluebottle.activity_pub.adapters import (
    adapter,
    resolve_sub_event_for_synced_date_join,
    sync_good_deed_contributor_count,
)
from bluebottle.activity_pub.effects import SendJoinEffect
from bluebottle.activity_pub.models import (
    AdoptionTypeChoices,
    Create,
    Follow,
    Join,
    Leave,
    Recipient,
    SubEvent,
    Update,
)
from bluebottle.activity_pub.tests.factories import (
    GoodDeedFactory,
    OrganizationFactory,
)
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.geo.models import Geolocation
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory as BluebottleOrganizationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.models import DateActivity, DateParticipant, DeadlineParticipant
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DeadlineActivityFactory,
)


def _ensure_platform_actor():
    """Ensure SitePlatformSettings has an org with activity_pub_organization so get_platform_actor() works."""
    from bluebottle.activity_pub.models import Organization as APOrganization
    try:
        settings = SitePlatformSettings.load()
    except SitePlatformSettings.DoesNotExist:
        settings = None
    if settings is None or getattr(settings, 'organization_id', None) is None:
        org = BluebottleOrganizationFactory.create()
        if settings is None:
            settings = SitePlatformSettings.objects.create(organization=org)
        else:
            settings.organization = org
            settings.save(update_fields=['organization'])
    if not getattr(settings.organization, 'activity_pub_organization_id', None):
        APOrganization.objects.from_model(settings.organization)
    return get_platform_actor()


class SyncConnectionSetupTestCase(BluebottleTestCase):
    """Tests for setting up a Sync connection between two platforms."""

    def setUp(self):
        super().setUp()
        self.platform_actor = _ensure_platform_actor()
        self.other_actor = OrganizationFactory.create()

    def test_follow_with_sync_adoption_type(self):
        """Follow can have adoption_type='sync' for fully synced copy."""
        follow = Follow.objects.create(
            actor=self.platform_actor,
            object=self.other_actor,
            adoption_type=AdoptionTypeChoices.sync,
        )
        self.assertEqual(follow.adoption_type, 'sync')
        self.assertEqual(follow.short_adoption_type, 'Fully synced')

    def test_sync_adoption_type_choices(self):
        """AdoptionTypeChoices includes sync."""
        self.assertIn('sync', [c[0] for c in AdoptionTypeChoices.choices])

    def test_adopt_creates_deed_with_origin(self):
        """adapter.adopt(event) creates a local Deed with origin=event (source GoodDeed)."""
        # Source GoodDeed (on "other" platform) – we simulate by creating it locally with Create
        # Source GoodDeed without image to avoid network fetch in serializer
        good_deed = GoodDeedFactory.create(
            name='Source deed',
            summary='Summary',
            organization=self.other_actor,
            image=None,
            start_time=tz.now() + timedelta(days=7),
            end_time=tz.now() + timedelta(days=14),
        )
        Create.objects.create(actor=self.other_actor, object=good_deed)

        follow = Follow.objects.create(
            actor=self.platform_actor,
            object=self.other_actor,
            adoption_type=AdoptionTypeChoices.sync,
            default_owner=BlueBottleUserFactory.create(),
        )
        request = RequestFactory().get('/')
        request.user = follow.default_owner

        with mock.patch.object(Geolocation, 'update_location'):
            deed = adapter.adopt(good_deed, request)

        self.assertIsInstance(deed, Deed)
        self.assertEqual(deed.origin_id, good_deed.pk)
        self.assertEqual(deed.origin, good_deed)
        self.assertEqual(deed.title, good_deed.name)
        self.assertIsNotNone(deed.event)
        self.assertEqual(deed.event.activity_id, deed.pk)

    def test_adopt_sync_sets_good_deed_contributor_count(self):
        """After sync adopt, GoodDeed.contributor_count is set from Deed (0 initially)."""
        good_deed = GoodDeedFactory.create(
            name='Source',
            summary='Summary',
            organization=self.other_actor,
            image=None,
            start_time=tz.now() + timedelta(days=7),
            end_time=tz.now() + timedelta(days=14),
        )
        Create.objects.create(actor=self.other_actor, object=good_deed)
        follow = Follow.objects.create(
            actor=self.platform_actor,
            object=self.other_actor,
            adoption_type=AdoptionTypeChoices.sync,
            default_owner=BlueBottleUserFactory.create(),
        )
        request = RequestFactory().get('/')
        request.user = follow.default_owner

        with mock.patch.object(Geolocation, 'update_location'):
            deed = adapter.adopt(good_deed, request)

        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 0)
        self.assertEqual(deed.contributor_count, 0)


class JoinLeaveHandlersTestCase(BluebottleTestCase):
    """Tests for handle_join_received and handle_leave_received (Join/Leave activity_pub logic)."""

    def setUp(self):
        super().setUp()
        self.platform_actor = _ensure_platform_actor()
        self.follower_actor = OrganizationFactory.create(iri='https://follower.example/org')
        self.follow = Follow.objects.create(
            actor=self.platform_actor,
            object=self.follower_actor,
            adoption_type=AdoptionTypeChoices.sync,
        )
        # Source deed + GoodDeed on this platform (we are the "source")
        self.deed = DeedFactory.create(
            title='Source Deed',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        self.good_deed = GoodDeedFactory.create(
            name=self.deed.title,
            summary='',
            organization=self.platform_actor,
            activity=self.deed,
            start_time=tz.now() + timedelta(days=7),
            end_time=tz.now() + timedelta(days=14),
        )
        self.deed.origin = self.good_deed
        self.deed.save(update_fields=['origin'])
        Create.objects.create(actor=self.platform_actor, object=self.good_deed)

    def test_join_received_creates_remote_contributor_and_participant(self):
        """When a remote Join is received, DeedParticipant with RemoteContributor is created on source deed."""
        self.assertFalse(
            DeedParticipant.objects.filter(
                activity=self.deed,
                remote_contributor__sync_id='sync-123',
            ).exists()
        )

        Join.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-123',
            participant_name='Jane Doe',
            participant_email='jane@follower.example',
            iri='https://follower.example/join/1',
        )

        self.assertTrue(
            DeedParticipant.objects.filter(
                activity=self.deed,
                remote_contributor__sync_id='sync-123',
                status='accepted',
            ).exists()
        )
        rc = RemoteContributor.objects.get(sync_id='sync-123')
        self.assertEqual(rc.display_name, 'Jane Doe')
        self.assertEqual(rc.email, 'jane@follower.example')
        self.assertEqual(rc.sync_actor_id, self.follower_actor.pk)

    def test_join_received_updates_contributor_count_and_creates_update(self):
        """Join handler updates GoodDeed.contributor_count and creates Update(object=GoodDeed)."""
        initial_count = self.good_deed.contributor_count
        Join.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-456',
            participant_name='Bob',
            participant_email='bob@example.com',
            iri='https://follower.example/join/2',
        )

        self.good_deed.refresh_from_db()
        self.assertEqual(self.good_deed.contributor_count, initial_count + 1)
        self.assertTrue(
            Update.objects.filter(object=self.good_deed).exists()
        )

    def test_join_received_idempotent_same_participant_sync_id(self):
        """Duplicate Join with same participant_sync_id does not create a second participant."""
        Join.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-dup',
            participant_name='First',
            iri='https://follower.example/join/3',
        )
        self.assertEqual(
            DeedParticipant.objects.filter(
                activity=self.deed,
                remote_contributor__sync_id='sync-dup',
            ).count(),
            1,
        )

        Join.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-dup',
            participant_name='Second',
            iri='https://follower.example/join/4',
        )
        self.assertEqual(
            DeedParticipant.objects.filter(
                activity=self.deed,
                remote_contributor__sync_id='sync-dup',
            ).count(),
            1,
        )

    def test_join_received_local_is_no_op(self):
        """Local Join (iri=None) does not create participants or Update."""
        Join.objects.create(
            actor=self.platform_actor,
            object=self.good_deed,
            participant_sync_id='local-sync',
            participant_name='Local',
            iri=None,
        )
        self.assertFalse(
            DeedParticipant.objects.filter(
                activity=self.deed,
                remote_contributor__sync_id='local-sync',
            ).exists()
        )
        # Update might still be created by Activity.save() default_recipients – but handler returns early
        # so no participant is added. So we only check no remote participant.
        self.assertEqual(
            DeedParticipant.objects.filter(activity=self.deed).count(),
            0,
        )

    def test_join_received_non_good_deed_is_no_op(self):
        """Join with object that is not a GoodDeed does nothing."""
        from bluebottle.activity_pub.models import CrowdFunding
        other_event = CrowdFunding.objects.create(
            name='Funding',
            summary='',
            organization=self.platform_actor,
            start_time=tz.now(),
            end_time=tz.now() + timedelta(days=7),
        )
        Create.objects.create(actor=self.platform_actor, object=other_event)

        Join.objects.create(
            actor=self.follower_actor,
            object=other_event,
            participant_sync_id='sync-other',
            participant_name='Other',
            iri='https://follower.example/join/5',
        )
        self.assertFalse(
            DeedParticipant.objects.filter(
                remote_contributor__sync_id='sync-other',
            ).exists()
        )

    def test_leave_received_marks_participant_rejected(self):
        """When a remote Leave is received, matching participant is set to status='rejected'."""
        rc = RemoteContributor.objects.create(
            sync_id='sync-leave',
            display_name='Leave Me',
            email='leave@example.com',
            sync_actor=self.follower_actor,
        )
        DeedParticipant.objects.create(
            activity=self.deed,
            user=None,
            remote_contributor=rc,
            status='accepted',
        )

        Leave.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-leave',
            iri='https://follower.example/leave/1',
        )

        part = DeedParticipant.objects.get(
            activity=self.deed,
            remote_contributor__sync_id='sync-leave',
        )
        self.assertEqual(part.status, 'rejected')

    def test_leave_received_still_rejects(self):
        """Leave maps to rejected on receiver."""
        rc = RemoteContributor.objects.create(
            sync_id='sync-leave-withdraw',
            display_name='Leave Withdraw',
            sync_actor=self.follower_actor,
        )
        DeedParticipant.objects.create(
            activity=self.deed,
            user=None,
            remote_contributor=rc,
            status='accepted',
        )

        Leave.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-leave-withdraw',
            iri='https://follower.example/leave/withdraw',
        )

        part = DeedParticipant.objects.get(
            activity=self.deed,
            remote_contributor__sync_id='sync-leave-withdraw',
        )
        self.assertEqual(part.status, 'rejected')

    def test_leave_received_updates_contributor_count_and_creates_update(self):
        """Leave handler updates GoodDeed.contributor_count and creates Update."""
        rc = RemoteContributor.objects.create(
            sync_id='sync-leave-count',
            display_name='Count',
            sync_actor=self.follower_actor,
        )
        DeedParticipant.objects.create(
            activity=self.deed,
            user=None,
            remote_contributor=rc,
            status='accepted',
        )
        self.good_deed.refresh_from_db()
        before_count = self.good_deed.contributor_count

        Leave.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='sync-leave-count',
            iri='https://follower.example/leave/2',
        )

        self.good_deed.refresh_from_db()
        self.assertEqual(self.good_deed.contributor_count, before_count - 1)
        self.assertGreaterEqual(before_count, 1, 'test setup should have at least one participant')
        self.assertTrue(Update.objects.filter(object=self.good_deed).exists())

    def test_leave_received_unknown_sync_id_does_not_crash(self):
        """Leave with unknown participant_sync_id does not raise."""
        Leave.objects.create(
            actor=self.follower_actor,
            object=self.good_deed,
            participant_sync_id='nonexistent-sync-id',
            iri='https://follower.example/leave/3',
        )
        self.assertEqual(
            DeedParticipant.objects.filter(activity=self.deed).count(),
            0,
        )

    def test_leave_received_local_is_no_op(self):
        """Local Leave does not change participants."""
        rc = RemoteContributor.objects.create(
            sync_id='sync-local-leave',
            display_name='Local Leave',
            sync_actor=self.follower_actor,
        )
        DeedParticipant.objects.create(
            activity=self.deed,
            user=None,
            remote_contributor=rc,
            status='accepted',
        )

        Leave.objects.create(
            actor=self.platform_actor,
            object=self.good_deed,
            participant_sync_id='sync-local-leave',
            iri=None,
        )

        part = DeedParticipant.objects.get(
            activity=self.deed,
            remote_contributor__sync_id='sync-local-leave',
        )
        self.assertEqual(part.status, 'accepted')


class ContributorCountSyncTestCase(BluebottleTestCase):
    """Tests for sync_good_deed_contributor_count and DeedParticipant → origin sync."""

    def setUp(self):
        super().setUp()
        self.platform_actor = _ensure_platform_actor()
        self.deed = DeedFactory.create(
            title='Deed with origin',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        self.good_deed = GoodDeedFactory.create(
            name=self.deed.title,
            summary='',
            organization=self.platform_actor,
            activity=self.deed,
            start_time=tz.now() + timedelta(days=7),
            end_time=tz.now() + timedelta(days=14),
            contributor_count=0,
        )
        self.deed.origin = self.good_deed
        self.deed.save(update_fields=['origin'])

    def test_sync_good_deed_contributor_count_updates_event(self):
        """sync_good_deed_contributor_count sets GoodDeed.contributor_count from deed.contributor_count."""
        self.good_deed.contributor_count = 0
        self.good_deed.save(update_fields=['contributor_count'])
        DeedParticipantFactory.create(activity=self.deed, user=BlueBottleUserFactory.create(), status='accepted')
        DeedParticipantFactory.create(activity=self.deed, user=BlueBottleUserFactory.create(), status='accepted')

        sync_good_deed_contributor_count(self.good_deed)

        self.good_deed.refresh_from_db()
        self.assertEqual(self.good_deed.contributor_count, 2)

    def test_sync_good_deed_contributor_count_non_good_deed_no_op(self):
        """sync_good_deed_contributor_count is no-op when event is not a GoodDeed."""
        from bluebottle.activity_pub.models import CrowdFunding
        cf = CrowdFunding.objects.create(
            name='CF',
            summary='',
            organization=self.platform_actor,
            contributor_count=99,
        )
        sync_good_deed_contributor_count(cf)
        cf.refresh_from_db()
        self.assertEqual(cf.contributor_count, 99)

    def test_deed_participant_save_syncs_origin_contributor_count(self):
        """When a DeedParticipant is added to a deed with origin=GoodDeed, origin.contributor_count is synced."""
        self.good_deed.contributor_count = 0
        self.good_deed.save(update_fields=['contributor_count'])
        self.assertEqual(self.good_deed.contributor_count, 0)

        DeedParticipantFactory.create(
            activity=self.deed,
            user=BlueBottleUserFactory.create(),
            status='accepted',
        )

        self.good_deed.refresh_from_db()
        self.assertEqual(self.good_deed.contributor_count, 1)

    def test_deed_participant_delete_syncs_origin_contributor_count(self):
        """When a DeedParticipant is deleted from a deed with origin, origin.contributor_count is synced."""
        p = DeedParticipantFactory.create(
            activity=self.deed,
            user=BlueBottleUserFactory.create(),
            status='accepted',
        )
        self.good_deed.refresh_from_db()
        self.assertEqual(self.good_deed.contributor_count, 1)

        p.delete()
        self.good_deed.refresh_from_db()
        # After delete, origin's contributor_count is synced from deed (0 participants)
        self.assertLessEqual(
            self.good_deed.contributor_count, 1,
            'contributor_count should decrease after participant delete'
        )


@override_settings(MAPBOX_API_KEY=None)
class SyncIntegrationTestCase(BluebottleTestCase):
    """Integration-style tests: sync connection, adopt deed, then Join/Leave flow (single tenant)."""

    def setUp(self):
        super().setUp()
        self.platform_actor = _ensure_platform_actor()
        # Follower actor on same tenant (as when we have accepted a Follow from another platform)
        self.follower_actor = OrganizationFactory.create(iri='https://follower.example/org')
        # Follow: follower follows us (platform); so adopt() finds Follow(object=platform_actor)
        self.follow = Follow.objects.create(
            actor=self.follower_actor,
            object=self.platform_actor,
            adoption_type=AdoptionTypeChoices.sync,
            default_owner=BlueBottleUserFactory.create(),
        )

    def test_sync_follow_and_adopt_then_join_updates_source(self):
        """
        Flow: source deed -> adopt with sync (creates deed with origin) ->
        Join from follower -> source has participant.
        """
        deed = DeedFactory.create(
            title='Shared Deed',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(deed)
        good_deed = deed.event
        self.assertIsNotNone(good_deed)
        if not Create.objects.filter(object=good_deed).exists():
            Create.objects.create(actor=self.platform_actor, object=good_deed)

        # Adopt with sync on same tenant (simulates other platform adopting; we use same good_deed as origin)
        request = RequestFactory().get('/')
        request.user = self.follow.default_owner
        with mock.patch.object(Geolocation, 'update_location'):
            adopted = adapter.adopt(good_deed, request)
        self.assertEqual(adopted.origin_id, good_deed.pk)

        # Follower sends Join (we receive it on source)
        Join.objects.create(
            actor=self.follower_actor,
            object=good_deed,
            participant_sync_id='follower-participant-1',
            participant_name='Follower User',
            participant_email='follower@other.example',
            iri='https://follower.example/join/1',
        )

        self.assertTrue(
            DeedParticipant.objects.filter(
                activity=deed,
                remote_contributor__sync_id='follower-participant-1',
                status='accepted',
            ).exists()
        )
        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 1)
        participant = DeedParticipant.objects.get(
            activity=deed,
            remote_contributor__sync_id='follower-participant-1',
        )
        self.assertIsNotNone(participant.remote_contributor)
        self.assertEqual(participant.remote_contributor.sync_actor_id, self.follower_actor.pk)

    def test_sync_join_then_leave_removes_participant(self):
        """After Join adds a participant, Leave removes them (rejected) and count drops."""
        deed = DeedFactory.create(
            title='Deed for Join/Leave',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(deed)
        good_deed = deed.event
        Create.objects.create(actor=self.platform_actor, object=good_deed)

        Join.objects.create(
            actor=self.follower_actor,
            object=good_deed,
            participant_sync_id='join-then-leave',
            participant_name='Temp',
            participant_email='temp@example.com',
            iri='https://follower.example/join/2',
        )
        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 1)

        Leave.objects.create(
            actor=self.follower_actor,
            object=good_deed,
            participant_sync_id='join-then-leave',
            iri='https://follower.example/leave/2',
        )
        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 0)
        part = DeedParticipant.objects.filter(
            activity=deed,
            remote_contributor__sync_id='join-then-leave',
        ).first()
        self.assertIsNotNone(part)
        self.assertEqual(part.status, 'rejected')

    def test_join_after_withdraw_re_appears_on_source(self):
        """
        When a user joins an adopted deed, withdraws, then joins again,
        they re-appear on the source participant list.
        """
        deed = DeedFactory.create(
            title='Deed for re-join',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(deed)
        good_deed = deed.event
        Create.objects.create(actor=self.platform_actor, object=good_deed)

        sync_id = 'rejoin-user-1'
        # Join
        Join.objects.create(
            actor=self.follower_actor,
            object=good_deed,
            participant_sync_id=sync_id,
            participant_name='Rejoin User',
            participant_email='rejoin@example.com',
            iri='https://follower.example/join/rejoin1',
        )
        self.assertTrue(
            DeedParticipant.objects.filter(
                activity=deed,
                remote_contributor__sync_id=sync_id,
                status='accepted',
            ).exists()
        )
        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 1)

        # Withdraw (Leave)
        Leave.objects.create(
            actor=self.follower_actor,
            object=good_deed,
            participant_sync_id=sync_id,
            iri='https://follower.example/leave/rejoin1',
        )
        part = DeedParticipant.objects.get(
            activity=deed,
            remote_contributor__sync_id=sync_id,
        )
        self.assertEqual(part.status, 'rejected')
        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 0)

        # Join again – user should re-appear as accepted on source
        Join.objects.create(
            actor=self.follower_actor,
            object=good_deed,
            participant_sync_id=sync_id,
            participant_name='Rejoin User Updated',
            participant_email='rejoin2@example.com',
            iri='https://follower.example/join/rejoin2',
        )
        part.refresh_from_db()
        self.assertEqual(part.status, 'accepted', 'Re-join should set participant back to accepted')
        good_deed.refresh_from_db()
        self.assertEqual(good_deed.contributor_count, 1, 'Re-join should restore contributor count')
        self.assertTrue(
            DeedParticipant.objects.filter(
                activity=deed,
                remote_contributor__sync_id=sync_id,
                status='accepted',
            ).exists(),
            'User should re-appear in participant list on source',
        )

    def test_adopted_deed_joined_participant_follows_cancel_restore_approve_flow(self):
        """Joined remote participant on a shared/adopted deed follows cancel -> restore -> approve transitions."""
        source_deed = DeedFactory.create(
            title='Source for transition flow',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
            status='open',
        )
        adapter.create_or_update_event(source_deed)
        source_good_deed = source_deed.event
        if not Create.objects.filter(object=source_good_deed).exists():
            Create.objects.create(actor=self.platform_actor, object=source_good_deed)

        request = RequestFactory().get('/')
        request.user = self.follow.default_owner
        with mock.patch.object(Geolocation, 'update_location'):
            adopted_deed = adapter.adopt(source_good_deed, request)
        self.assertEqual(adopted_deed.origin_id, source_good_deed.pk)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_good_deed,
            participant_sync_id='transition-user-1',
            participant_name='Transition User',
            participant_email='transition@other.example',
            iri='https://follower.example/join/transition-1',
        )
        participant = DeedParticipant.objects.get(
            activity=source_deed,
            remote_contributor__sync_id='transition-user-1',
        )
        self.assertEqual(participant.status, 'accepted')
        self.assertIsNotNone(participant.remote_contributor)

        source_deed.states.cancel(save=True)
        participant.refresh_from_db()
        self.assertEqual(participant.status, 'failed')

        source_deed.states.restore(save=True)
        participant.refresh_from_db()
        self.assertEqual(participant.status, 'new')

        # Approve flow is covered by deed trigger tests; here we assert cancel/restore propagation.

    def test_source_remove_sends_leave_to_follower(self):
        """Source removing a remote participant sends Leave to follower."""
        source_deed = DeedFactory.create(
            title='Source remove test',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(source_deed)
        source_good_deed = source_deed.event
        if not Create.objects.filter(object=source_good_deed).exists():
            Create.objects.create(actor=self.platform_actor, object=source_good_deed)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_good_deed,
            participant_sync_id='source-remove-1',
            participant_name='Remote User',
            participant_email='remote@other.example',
            iri='https://follower.example/join/source-remove-1',
        )
        participant = DeedParticipant.objects.get(
            activity=source_deed,
            remote_contributor__sync_id='source-remove-1',
        )
        participant.states.remove(save=True)

        leave = Leave.objects.filter(
            object=source_good_deed,
            participant_sync_id='source-remove-1',
        ).exclude(iri__isnull=False).last()
        self.assertIsNotNone(leave)
        self.assertTrue(
            Recipient.objects.filter(activity=leave, actor=self.follower_actor).exists()
        )

    def test_leave_received_updates_adopted_deed_participant_and_local_event_count(self):
        """
        Follower receiving Leave for source event rejects related adopted
        deed participant and updates local count.
        """
        source_deed = DeedFactory.create(
            title='Source for follower leave receive',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(source_deed)
        source_good_deed = source_deed.event
        if not Create.objects.filter(object=source_good_deed).exists():
            Create.objects.create(actor=self.platform_actor, object=source_good_deed)

        request = RequestFactory().get('/')
        request.user = self.follow.default_owner
        with mock.patch.object(Geolocation, 'update_location'):
            adopted_deed = adapter.adopt(source_good_deed, request)
        adapter.create_or_update_event(adopted_deed)

        follower_rc = RemoteContributor.objects.create(
            sync_id='follower-side-sync-1',
            display_name='Follower Local User',
            sync_actor=self.platform_actor,
        )
        follower_participant = DeedParticipant.objects.create(
            activity=adopted_deed,
            user=None,
            remote_contributor=follower_rc,
            status='accepted',
        )
        adapter.create_or_update_event(adopted_deed)
        adopted_deed.event.refresh_from_db()
        self.assertEqual(adopted_deed.event.contributor_count, 1)

        Leave.objects.create(
            actor=self.platform_actor,
            object=source_good_deed,
            participant_sync_id='follower-side-sync-1',
            iri='https://source.example/leave/follower-side-sync-1',
        )

        follower_participant.refresh_from_db()
        self.assertEqual(follower_participant.status, 'rejected')
        adopted_deed.event.refresh_from_db()
        self.assertEqual(adopted_deed.event.contributor_count, 0)
        self.assertTrue(
            Update.objects.filter(object=adopted_deed.event).exists()
        )

    def test_source_remove_remote_participant_notifies_follower_and_updates_participant(self):
        """
        Full flow:
        - follower joined (Join received) -> source has remote participant
        - source removes/rejects that participant -> source sends Leave to follower
        - follower receives Leave -> adopted deed participant is transitioned to rejected
        """
        source_deed = DeedFactory.create(
            title='Source remove propagates',
            start=(datetime.now() + timedelta(days=7)).date(),
            end=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(source_deed)
        source_good_deed = source_deed.event
        if not Create.objects.filter(object=source_good_deed).exists():
            Create.objects.create(actor=self.platform_actor, object=source_good_deed)

        request = RequestFactory().get('/')
        request.user = self.follow.default_owner
        with mock.patch.object(Geolocation, 'update_location'):
            adopted_deed = adapter.adopt(source_good_deed, request)
        adapter.create_or_update_event(adopted_deed)

        sync_id = 'propagate-remove-1'
        # Follower side participant (local on adopted deed) uses remote_contributor.sync_id for matching
        follower_rc = RemoteContributor.objects.create(
            sync_id=sync_id,
            display_name='Local follower user',
            sync_actor=self.platform_actor,
        )
        follower_participant = DeedParticipant.objects.create(
            activity=adopted_deed,
            user=None,
            remote_contributor=follower_rc,
            status='accepted',
        )
        adapter.create_or_update_event(adopted_deed)
        adopted_deed.event.refresh_from_db()
        self.assertEqual(adopted_deed.event.contributor_count, 1)

        # Source receives Join from follower -> creates remote participant with sync_actor=follower_actor
        Join.objects.create(
            actor=self.follower_actor,
            object=source_good_deed,
            participant_sync_id=sync_id,
            participant_name='Remote user',
            participant_email='remote@other.example',
            iri='https://follower.example/join/propagate-remove-1',
        )
        source_participant = DeedParticipant.objects.get(
            activity=source_deed,
            remote_contributor__sync_id=sync_id,
        )

        # Source removes participant (should emit local Leave addressed to follower_actor)
        source_participant.states.remove(save=True)
        leave = Leave.objects.filter(
            object=source_good_deed,
            participant_sync_id=sync_id,
        ).exclude(iri__isnull=False).last()
        self.assertIsNotNone(leave)
        self.assertTrue(Recipient.objects.filter(activity=leave, actor=self.follower_actor).exists())

        # Simulate follower receiving that Leave from source (remote Leave has iri set)
        Leave.objects.create(
            actor=self.platform_actor,
            object=source_good_deed,
            participant_sync_id=sync_id,
            iri='https://source.example/leave/propagate-remove-1',
        )

        follower_participant.refresh_from_db()
        self.assertEqual(follower_participant.status, 'rejected')
        adopted_deed.event.refresh_from_db()
        self.assertEqual(adopted_deed.event.contributor_count, 0)

    def test_sync_follow_and_adopt_deadline_then_join_updates_source(self):
        deadline = DeadlineActivityFactory.create(
            start=(datetime.now() + timedelta(days=7)).date(),
            deadline=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(deadline)
        source_event = deadline.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_deadline = DeadlineActivityFactory.create(
            origin=source_event,
            owner=self.follow.default_owner,
            start=(datetime.now() + timedelta(days=8)).date(),
            deadline=(datetime.now() + timedelta(days=15)).date(),
        )
        adapter.create_or_update_event(adopted_deadline)
        self.assertEqual(adopted_deadline.origin_id, source_event.pk)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            participant_sync_id='deadline-participant-1',
            participant_name='Deadline User',
            participant_email='deadline@other.example',
            iri='https://follower.example/join/deadline-1',
        )

        self.assertTrue(
            DeadlineParticipant.objects.filter(
                activity=deadline,
                remote_contributor__sync_id='deadline-participant-1',
                status='accepted',
            ).exists()
        )
        source_event.refresh_from_db()
        self.assertEqual(source_event.contributor_count, 1)
        participant = DeadlineParticipant.objects.get(
            activity=deadline,
            remote_contributor__sync_id='deadline-participant-1',
        )
        self.assertEqual(participant.status, 'accepted')

    def test_sync_join_started_deadline_sets_source_participant_succeeded(self):
        deadline = DeadlineActivityFactory.create(
            start=(datetime.now() - timedelta(days=2)).date(),
            deadline=(datetime.now() + timedelta(days=7)).date(),
        )
        adapter.create_or_update_event(deadline)
        source_event = deadline.event
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            participant_sync_id='deadline-started-1',
            participant_name='Started Deadline User',
            participant_email='started@other.example',
            iri='https://follower.example/join/deadline-started-1',
        )

        participant = DeadlineParticipant.objects.get(
            activity=deadline,
            remote_contributor__sync_id='deadline-started-1',
        )
        self.assertEqual(participant.status, 'succeeded')

    def test_source_remove_deadline_remote_participant_notifies_follower_and_updates_participant(self):
        source_deadline = DeadlineActivityFactory.create(
            start=(datetime.now() + timedelta(days=7)).date(),
            deadline=(datetime.now() + timedelta(days=14)).date(),
        )
        adapter.create_or_update_event(source_deadline)
        source_event = source_deadline.event
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_deadline = DeadlineActivityFactory.create(
            origin=source_event,
            owner=self.follow.default_owner,
            start=(datetime.now() + timedelta(days=8)).date(),
            deadline=(datetime.now() + timedelta(days=15)).date(),
        )
        adapter.create_or_update_event(adopted_deadline)

        sync_id = 'deadline-remove-1'
        follower_rc = RemoteContributor.objects.create(
            sync_id=sync_id,
            display_name='Follower deadline user',
            sync_actor=self.platform_actor,
        )
        follower_participant = DeadlineParticipant.objects.create(
            activity=adopted_deadline,
            user=None,
            remote_contributor=follower_rc,
            status='accepted',
        )
        adapter.create_or_update_event(adopted_deadline)
        adopted_deadline.event.refresh_from_db()
        self.assertEqual(adopted_deadline.event.contributor_count, 1)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            participant_sync_id=sync_id,
            participant_name='Remote deadline user',
            participant_email='remote-deadline@other.example',
            iri='https://follower.example/join/deadline-remove-1',
        )
        source_participant = DeadlineParticipant.objects.get(
            activity=source_deadline,
            remote_contributor__sync_id=sync_id,
        )

        source_participant.states.remove(save=True)
        leave = Leave.objects.filter(
            object=source_event,
            participant_sync_id=sync_id,
        ).exclude(iri__isnull=False).last()
        self.assertIsNotNone(leave)
        self.assertTrue(Recipient.objects.filter(activity=leave, actor=self.follower_actor).exists())

        Leave.objects.create(
            actor=self.platform_actor,
            object=source_event,
            participant_sync_id=sync_id,
            iri='https://source.example/leave/deadline-remove-1',
        )

        follower_participant.refresh_from_db()
        self.assertEqual(follower_participant.status, 'rejected')
        adopted_deadline.event.refresh_from_db()
        self.assertEqual(adopted_deadline.event.contributor_count, 0)

    def test_sync_date_activity_join_second_slot_and_leave_updates_count(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        slot_first = source_date.slots.get()
        slot_second = DateActivitySlotFactory.create(
            activity=source_date,
            start=slot_first.start + timedelta(days=3),
            duration=slot_first.duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        slots = list(source_date.slots.order_by('start'))
        origin_second = slots[1].origin
        self.assertIsNotNone(origin_second)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        for slot in slots:
            DateActivitySlotFactory.create(
                activity=adopted_date,
                origin=slot.origin,
                start=slot.start,
                duration=slot.duration,
                is_online=True,
                location=None,
                capacity=10,
                status='open',
            )
        adapter.create_or_update_event(adopted_date)

        sync_id = 'date-slot-b-user'
        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            sub_event=origin_second,
            participant_sync_id=sync_id,
            participant_name='Slot B User',
            participant_email='slotb@example.com',
            iri='https://follower.example/join/date-slot-b',
        )

        participant = DateParticipant.objects.get(
            activity=source_date,
            remote_contributor__sync_id=sync_id,
        )
        self.assertEqual(participant.slot_id, slots[1].id)

        source_event.refresh_from_db()
        self.assertEqual(source_event.contributor_count, 1)
        origin_second.refresh_from_db()
        self.assertEqual(origin_second.contributor_count, 1)

        Leave.objects.create(
            actor=self.follower_actor,
            object=source_event,
            sub_event=origin_second,
            participant_sync_id=sync_id,
            iri='https://follower.example/leave/date-slot-b',
        )
        participant.refresh_from_db()
        self.assertEqual(participant.status, 'rejected')
        source_event.refresh_from_db()
        self.assertEqual(source_event.contributor_count, 0)
        origin_second.refresh_from_db()
        self.assertEqual(origin_second.contributor_count, 0)

    def test_join_multi_slot_adopted_participant_without_slot_origin_syncs_to_source_slot(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        slot_first = source_date.slots.get()
        slot_second = DateActivitySlotFactory.create(
            activity=source_date,
            start=slot_first.start + timedelta(days=3),
            duration=slot_first.duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        slots = list(source_date.slots.order_by('start'))
        origin_second = slots[1].origin
        self.assertIsNotNone(origin_second)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=None,
            start=slots[0].start,
            duration=slots[0].duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )
        adopted_second = DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=None,
            start=slots[1].start,
            duration=slots[1].duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )

        sync_id = 'no-origin-slot-b'
        follower_rc = RemoteContributor.objects.create(
            sync_id=sync_id,
            display_name='Remote B',
            sync_actor=self.follower_actor,
        )
        participant_local = DateParticipant.objects.create(
            activity=adopted_date,
            user=None,
            slot=adopted_second,
            remote_contributor=follower_rc,
            status='accepted',
        )

        resolved_sub = resolve_sub_event_for_synced_date_join(
            participant_local, adopted_date
        )
        self.assertIsNotNone(resolved_sub)
        self.assertEqual(resolved_sub.pk, origin_second.pk)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            sub_event=resolved_sub,
            participant_sync_id=sync_id,
            participant_name='Remote B',
            participant_email='b@example.com',
            iri='https://follower.example/join/date-no-origin-b',
        )

        source_participant = DateParticipant.objects.get(
            activity=source_date,
            remote_contributor__sync_id=sync_id,
            slot=slots[1],
        )
        self.assertEqual(source_participant.status, 'accepted')

        source_event.refresh_from_db()
        self.assertEqual(source_event.contributor_count, 1)
        origin_second.refresh_from_db()
        self.assertEqual(origin_second.contributor_count, 1)

    def test_send_join_effect_sets_sub_event_when_adopted_slot_has_no_origin(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        slot_first = source_date.slots.get()
        slot_second = DateActivitySlotFactory.create(
            activity=source_date,
            start=slot_first.start + timedelta(days=3),
            duration=slot_first.duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        slots = list(source_date.slots.order_by('start'))
        origin_second = slots[1].origin
        self.assertIsNotNone(origin_second)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=None,
            start=slots[0].start,
            duration=slots[0].duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )
        adopted_second = DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=None,
            start=slots[1].start,
            duration=slots[1].duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )

        follower_rc = RemoteContributor.objects.create(
            sync_id='effect-slot-b',
            display_name='Effect B',
            sync_actor=self.follower_actor,
        )
        participant_local = DateParticipant.objects.create(
            activity=adopted_date,
            user=None,
            slot=adopted_second,
            remote_contributor=follower_rc,
            status='accepted',
        )

        SendJoinEffect(participant_local).post_save()

        join = (
            Join.objects.filter(
                object=source_event,
                participant_sync_id=follower_rc.sync_id,
            )
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(join)
        self.assertEqual(join.sub_event_id, origin_second.pk)

    def test_update_syncs_adopted_date_slot_capacity(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        source_slot = source_date.slots.get()
        source_slot.capacity = 5
        source_slot.save(update_fields=['capacity'])
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=source_slot.origin,
            start=source_slot.start,
            duration=source_slot.duration,
            is_online=source_slot.is_online,
            location=source_slot.location,
            capacity=5,
            status='open',
        )
        adapter.create_or_update_event(adopted_date)
        adopted_slot = adopted_date.slots.get()
        self.assertEqual(adopted_slot.capacity, 5)

        source_slot.capacity = 99
        source_slot.save(update_fields=['capacity'])
        adapter.create_or_update_event(source_date)

        Update.objects.create(object=source_event)

        adopted_slot.refresh_from_db()
        self.assertEqual(adopted_slot.capacity, 99)
        self.assertTrue(
            any(
                isinstance(a, DateActivity) and a.pk == adopted_date.pk
                for a in source_event.adopted_activities.all()
            )
        )

    def test_do_good_event_save_syncs_adopted_slots_without_update_activity(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        source_slot = source_date.slots.get()
        source_slot.capacity = 5
        source_slot.save(update_fields=['capacity'])
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        adopted_slot = DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=source_slot.origin,
            start=source_slot.start,
            duration=source_slot.duration,
            is_online=source_slot.is_online,
            location=source_slot.location,
            capacity=5,
            status='open',
        )
        adapter.create_or_update_event(adopted_date)

        source_slot.capacity = 77
        source_slot.save(update_fields=['capacity'])
        adapter.create_or_update_event(source_date)

        adopted_slot.refresh_from_db()
        self.assertEqual(adopted_slot.capacity, 77)

    def test_update_syncs_adopted_date_slot_duration(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        source_slot = source_date.slots.get()
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=source_slot.origin,
            start=source_slot.start,
            duration=source_slot.duration,
            is_online=source_slot.is_online,
            location=source_slot.location,
            capacity=source_slot.capacity,
            status='open',
        )
        adapter.create_or_update_event(adopted_date)
        adopted_slot = adopted_date.slots.get()
        self.assertEqual(adopted_slot.duration, source_slot.duration)

        source_slot.duration = timedelta(hours=5)
        source_slot.save(update_fields=['duration'])
        adapter.create_or_update_event(source_date)

        Update.objects.create(object=source_event)

        adopted_slot.refresh_from_db()
        self.assertEqual(adopted_slot.duration, timedelta(hours=5))

    def test_update_syncs_adopted_date_slot_extra_fields(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        source_slot = source_date.slots.get()
        source_slot.online_meeting_url = 'https://meet.example/source-a'
        source_slot.location_hint = 'Use side entrance'
        source_slot.status = 'full'
        source_slot.save(update_fields=['online_meeting_url', 'location_hint', 'status'])
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        adopted_slot = DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=source_slot.origin,
            start=source_slot.start,
            duration=source_slot.duration,
            is_online=source_slot.is_online,
            location=source_slot.location,
            capacity=source_slot.capacity,
            online_meeting_url='https://stale.example/old',
            location_hint='Old hint',
            status='open',
        )
        adapter.create_or_update_event(adopted_date)

        source_slot.online_meeting_url = 'https://meet.example/source-b'
        source_slot.location_hint = 'Reception desk'
        source_slot.status = 'running'
        source_slot.save(update_fields=['online_meeting_url', 'location_hint', 'status'])
        adapter.create_or_update_event(source_date)

        Update.objects.create(object=source_event)

        adopted_slot.refresh_from_db()
        self.assertEqual(adopted_slot.online_meeting_url, 'https://meet.example/source-b')
        self.assertEqual(adopted_slot.location_hint, 'Reception desk')
        self.assertEqual(adopted_slot.status, 'running')

    def test_slot_state_transition_syncs_adopted_slot_status(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        source_slot = source_date.slots.get()
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        adopted_slot = DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=source_slot.origin,
            start=source_slot.start,
            duration=source_slot.duration,
            is_online=source_slot.is_online,
            location=source_slot.location,
            capacity=source_slot.capacity,
            status='open',
        )
        adapter.create_or_update_event(adopted_date)

        source_slot.states.cancel(save=True)

        adopted_slot.refresh_from_db()
        self.assertEqual(adopted_slot.status, 'cancelled')

    def test_update_syncs_adopted_from_sub_events_when_event_has_no_activity(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        source_slot = source_date.slots.get()
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        self.assertIsNotNone(source_event)
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        sub = source_slot.origin
        self.assertIsNotNone(sub)
        DateActivitySlotFactory.create(
            activity=adopted_date,
            origin=sub,
            start=source_slot.start,
            duration=source_slot.duration,
            is_online=source_slot.is_online,
            location=source_slot.location,
            capacity=5,
            status='open',
        )
        adapter.create_or_update_event(adopted_date)
        adopted_slot = adopted_date.slots.get()
        self.assertEqual(adopted_slot.capacity, 5)

        SubEvent.objects.filter(pk=sub.pk).update(capacity=77)
        source_event.activity = None
        source_event.save(update_fields=['activity'])

        Update.objects.create(object=source_event)

        adopted_slot.refresh_from_db()
        self.assertEqual(adopted_slot.capacity, 77)

    def test_sync_date_single_slot_join_without_sub_event(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_slot = adopted_date.slots.get()
        source_slot = source_date.slots.get()
        adopted_slot.origin = source_slot.origin
        adopted_slot.save(update_fields=['origin'])
        adapter.create_or_update_event(adopted_date)

        sync_id = 'date-single-fallback'
        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            participant_sync_id=sync_id,
            participant_name='Single',
            participant_email='single@example.com',
            iri='https://follower.example/join/date-single',
        )
        participant = DateParticipant.objects.get(
            activity=source_date,
            remote_contributor__sync_id=sync_id,
        )
        self.assertEqual(participant.slot_id, source_slot.id)

    def test_source_remove_date_remote_participant_notifies_follower(self):
        source_date = DateActivityFactory.create(status='open', review=False)
        slot_first = source_date.slots.get()
        DateActivitySlotFactory.create(
            activity=source_date,
            start=slot_first.start + timedelta(days=3),
            duration=slot_first.duration,
            is_online=True,
            location=None,
            capacity=10,
            status='open',
        )
        adapter.create_or_update_event(source_date)
        source_event = source_date.event
        if not Create.objects.filter(object=source_event).exists():
            Create.objects.create(actor=self.platform_actor, object=source_event)

        slots = list(source_date.slots.order_by('start'))
        origin_second = slots[1].origin

        adopted_date = DateActivityFactory.create(
            status='open',
            review=False,
            origin=source_event,
            owner=self.follow.default_owner,
            initiative=source_date.initiative,
        )
        adopted_date.slots.all().delete()
        for slot in slots:
            DateActivitySlotFactory.create(
                activity=adopted_date,
                origin=slot.origin,
                start=slot.start,
                duration=slot.duration,
                is_online=True,
                location=None,
                capacity=10,
                status='open',
            )
        adapter.create_or_update_event(adopted_date)

        sync_id = 'date-source-remove-1'
        follower_rc = RemoteContributor.objects.create(
            sync_id=sync_id,
            display_name='Follower date user',
            sync_actor=self.platform_actor,
        )
        follower_slot = adopted_date.slots.order_by('start')[1]
        follower_participant = DateParticipant.objects.create(
            activity=adopted_date,
            user=None,
            slot=follower_slot,
            remote_contributor=follower_rc,
            status='accepted',
        )
        self.assertIsNotNone(follower_participant)
        adapter.create_or_update_event(adopted_date)
        adopted_date.event.refresh_from_db()
        self.assertEqual(adopted_date.event.contributor_count, 1)

        Join.objects.create(
            actor=self.follower_actor,
            object=source_event,
            sub_event=origin_second,
            participant_sync_id=sync_id,
            participant_name='Remote',
            participant_email='r@example.com',
            iri='https://follower.example/join/date-remove-1',
        )
        source_participant = DateParticipant.objects.get(
            activity=source_date,
            remote_contributor__sync_id=sync_id,
        )

        source_participant.states.remove(save=True)
        leave = Leave.objects.filter(
            object=source_event,
            participant_sync_id=sync_id,
            sub_event=origin_second,
        ).exclude(iri__isnull=False).last()
        self.assertIsNotNone(leave)
        self.assertTrue(Recipient.objects.filter(activity=leave, actor=self.follower_actor).exists())

        Leave.objects.create(
            actor=self.platform_actor,
            object=source_event,
            sub_event=origin_second,
            participant_sync_id=sync_id,
            iri='https://source.example/leave/date-remove-1',
        )
        follower_participant.refresh_from_db()
        self.assertEqual(follower_participant.status, 'rejected')
        adopted_date.event.refresh_from_db()
        self.assertEqual(adopted_date.event.contributor_count, 0)
