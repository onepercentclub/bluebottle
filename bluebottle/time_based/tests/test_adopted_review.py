from django.urls import reverse

from bluebottle.activity_pub.tests.factories import (
    CreateFactory,
    DoGoodEventFactory,
    OrganizationFactory,
    SubEventFactory,
)
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase
from bluebottle.time_based.models import DateActivity
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    ScheduleRegistrationFactory,
    TeamFactory,
    TeamScheduleRegistrationFactory,
)


def adopt(activity):
    """Make `activity` adopted from a remote supplier platform."""
    event = DoGoodEventFactory.create(
        adopted=activity, iri=f'https://supplier.example.com/event/{activity.pk}'
    )
    CreateFactory.create(
        object=event,
        actor=OrganizationFactory.create(iri='https://supplier.example.com/org'),
    )
    if isinstance(activity, DateActivity):
        for slot in activity.slots.all():
            SubEventFactory.create(
                parent=event,
                adopted=slot,
                iri=f'https://supplier.example.com/sub-event/{slot.pk}',
            )
    activity.refresh_from_db()
    return event


class AdoptedActivityReviewTestCase:
    """
    On a consumer (adopted) activity with review enabled, joining must leave
    both registration and participant in 'new' — not auto-accepted.
    """

    activity_factory = None
    registration_factory = None

    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.activity_factory.create(
            initiative=self.initiative,
            review=True,
            capacity=4,
            registration_deadline=None,
            **self.activity_kwargs
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        adopt(self.activity)
        self.assertTrue(self.activity.is_adopted)

    @property
    def activity_kwargs(self):
        return {}

    def create_registration(self, as_user=None):
        user = BlueBottleUserFactory.create()
        return self.registration_factory.create(
            activity=self.activity,
            user=user,
            as_user=as_user or user,
        )


class DeadlineAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = DeadlineActivityFactory
    registration_factory = DeadlineRegistrationFactory

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        participant = registration.participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_participant_stays_new(self):
        user = BlueBottleUserFactory.create()
        participant = DeadlineParticipantFactory.create(
            activity=self.activity,
            user=user,
            as_user=self.admin_user,
        )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.registration.status, 'new')


class ScheduleAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = ScheduleActivityFactory
    registration_factory = ScheduleRegistrationFactory

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        participant = registration.participants.get()

        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_participant_stays_new(self):
        user = BlueBottleUserFactory.create()
        participant = ScheduleParticipantFactory.create(
            activity=self.activity,
            user=user,
            as_user=self.admin_user,
        )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.registration.status, 'new')


class PeriodicAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = PeriodicActivityFactory
    registration_factory = PeriodicRegistrationFactory

    # Periodic participants for adopted activities are not created on the consumer
    # (see CreateInitialPeriodicParticipantEffect.is_valid)
    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()

        self.assertEqual(registration.status, 'new')
        self.assertFalse(registration.participants.exists())

    def test_admin_adds_registration_stays_new(self):
        registration = self.create_registration(as_user=self.admin_user)

        self.assertEqual(registration.status, 'new')
        self.assertFalse(registration.participants.exists())


class DateAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = DateActivityFactory
    registration_factory = DateRegistrationFactory

    @property
    def activity_kwargs(self):
        return {'slots': []}

    def setUp(self):
        super(AdoptedActivityReviewTestCase, self).setUp()
        self.settings = InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )
        self.admin_user = BlueBottleUserFactory.create(is_staff=True)
        self.user = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory(owner=self.user)

        self.activity = self.activity_factory.create(
            initiative=self.initiative,
            review=True,
            capacity=4,
            registration_deadline=None,
            **self.activity_kwargs
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            is_online=True,
            location=None,
        )
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        adopt(self.activity)
        self.assertTrue(self.activity.is_adopted)

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        participant = DateParticipantFactory.create(
            activity=self.activity,
            slot=self.slot,
            registration=registration,
            user=registration.user,
            as_user=registration.user,
        )

        registration.refresh_from_db()
        self.assertEqual(registration.status, 'new')
        self.assertEqual(participant.status, 'new')

    def test_admin_adds_participant_stays_new(self):
        user = BlueBottleUserFactory.create()
        participant = DateParticipantFactory.create(
            activity=self.activity,
            slot=self.slot,
            user=user,
            registration=None,
            as_user=self.admin_user,
        )

        self.assertEqual(participant.status, 'new')
        self.assertEqual(participant.registration.status, 'new')


class TeamScheduleAdoptedReviewTestCase(AdoptedActivityReviewTestCase, BluebottleTestCase):
    activity_factory = ScheduleActivityFactory
    registration_factory = TeamScheduleRegistrationFactory

    def setUp(self):
        super().setUp()
        self.activity.team_activity = 'teams'
        self.activity.save()

    def test_user_joins_registration_stays_new(self):
        registration = self.create_registration()
        team = TeamFactory.create(
            registration=registration,
            activity=self.activity,
            user=registration.user,
        )
        self.assertEqual(registration.status, 'new')
        self.assertEqual(team.status, 'new')
        # Team slots, and so participants, are not created on the consumer
        # (see CreateTeamSlotEffect.is_local)
        self.assertFalse(team.team_members.get().participants.exists())


class AdoptedRegistrationPermissionTestCase(BluebottleTestCase):
    """
    The registration state machine must refuse review by consumer staff, but
    still allow the review result coming back from the supplier (no user).
    """

    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(activity_types=['deadlineactivity'])
        self.staff_user = BlueBottleUserFactory.create(is_staff=True)
        initiative = InitiativeFactory.create()
        self.activity = DeadlineActivityFactory.create(
            initiative=initiative,
            review=True,
            capacity=4,
            registration_deadline=None,
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        adopt(self.activity)

        user = BlueBottleUserFactory.create()
        self.registration = DeadlineRegistrationFactory.create(
            activity=self.activity, user=user, as_user=user
        )

    def test_staff_cannot_review(self):
        transitions = self.registration.states.possible_transitions(user=self.staff_user)
        self.assertNotIn(self.registration.states.transitions['accept'], transitions)
        self.assertNotIn(self.registration.states.transitions['reject'], transitions)

    def test_supplier_accept_still_possible(self):
        # Accept.save() in activity_pub calls this without a user
        self.registration.states.accept(save=True)
        self.assertEqual(self.registration.status, 'accepted')

    def test_supplier_reject_still_possible(self):
        # Reject.save() in activity_pub calls this without a user
        self.registration.states.reject(save=True)
        self.assertEqual(self.registration.status, 'rejected')


class ReviewAdminTestCase:
    """
    Admin pages for a pending registration on an activity with review enabled.
    With `adopted = True` (consumer) review must not be possible, it happens on
    the supplier. With `adopted = False` it should work as before.
    """

    adopted = True
    activity_factory = None
    registration_factory = None
    registration_admin = None

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(
            activity_types=[self.activity_factory._meta.model.__name__.lower()]
        )
        self.app.set_user(self.staff_member)

        initiative = InitiativeFactory.create()
        self.activity = self.activity_factory.create(
            initiative=initiative,
            review=True,
            capacity=4,
            registration_deadline=None,
            **self.activity_kwargs
        )
        self.setup_activity()
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        if self.adopted:
            adopt(self.activity)
            self.assertTrue(self.activity.is_adopted)

        self.registration = self.create_pending_registration()
        self.assertEqual(self.registration.status, 'new')

    @property
    def activity_kwargs(self):
        return {}

    def setup_activity(self):
        pass

    def create_pending_registration(self):
        user = BlueBottleUserFactory.create()
        return self.registration_factory.create(
            activity=self.activity, user=user, as_user=user
        )

    @property
    def registration_url(self):
        return reverse(
            f'admin:time_based_{self.registration_admin}_change',
            args=(self.registration.pk,)
        )

    def transition_url(self, name):
        return reverse(
            f'admin:time_based_{self.registration_admin}_state_transition',
            args=(self.registration.pk, 'states', name)
        )

    def assert_review_possible(self, possible):
        page = self.app.get(self.registration_url)
        self.assertEqual(page.status, '200 OK')
        for name in ('accept', 'reject'):
            links = page.html.find_all('a', href=self.transition_url(name))
            self.assertEqual(bool(links), possible, f'{name} transition shown: {bool(links)}')

    def test_registration_admin_review_transitions(self):
        self.assert_review_possible(not self.adopted)

    def test_accept_transition_url(self):
        page = self.app.get(self.transition_url('accept'))
        if self.adopted:
            self.assertEqual(page.status_code, 302)
            self.assertEqual(page.location, self.registration_url)
        else:
            self.assertEqual(page.status_code, 200)

    def test_confirm_accept_transition(self):
        page = self.app.post(
            self.transition_url('accept'),
            {'confirm': True, 'send_messages': False}
        )
        self.assertEqual(page.status_code, 302)
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status, 'new' if self.adopted else 'accepted'
        )


class RegistrationInfoTests:
    """
    The registration info on the participant (or team) admin page links to the
    review of the registration, except on adopted activities.
    """

    info_admin = None

    @property
    def info_object(self):
        return self.registration.participants.get()

    def test_registration_info_review_button(self):
        page = self.app.get(
            reverse(f'admin:time_based_{self.info_admin}_change', args=(self.info_object.pk,))
        )
        self.assertEqual(page.status, '200 OK')
        button = page.html.find('a', {'class': 'button', 'href': self.registration_url})
        self.assertEqual(bool(button), not self.adopted)
        self.assertEqual(
            'Participants are reviewed on the supplier platform.' in page.text,
            self.adopted
        )


class DeadlineReviewAdmin:
    activity_factory = DeadlineActivityFactory
    registration_factory = DeadlineRegistrationFactory
    registration_admin = 'deadlineregistration'
    info_admin = 'deadlineparticipant'


class DeadlineAdoptedReviewAdminTestCase(
    DeadlineReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    def test_admin_added_participant_has_no_review_button(self):
        # Scenario from BB-30275: participant added by staff in the consumer admin
        participant = DeadlineParticipantFactory.create(
            activity=self.activity,
            user=BlueBottleUserFactory.create(),
            as_user=self.staff_member,
        )
        self.assertEqual(participant.registration.status, 'new')

        page = self.app.get(
            reverse('admin:time_based_deadlineparticipant_change', args=(participant.pk,))
        )
        self.assertEqual(page.status, '200 OK')
        self.assertNotIn('Review candidate', page.text)


class DeadlineLocalReviewAdminTestCase(
    DeadlineReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    adopted = False


class ScheduleReviewAdmin:
    activity_factory = ScheduleActivityFactory
    registration_factory = ScheduleRegistrationFactory
    registration_admin = 'scheduleregistration'
    info_admin = 'scheduleparticipant'


class ScheduleAdoptedReviewAdminTestCase(
    ScheduleReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    pass


class ScheduleLocalReviewAdminTestCase(
    ScheduleReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    adopted = False


class PeriodicReviewAdmin:
    activity_factory = PeriodicActivityFactory
    registration_factory = PeriodicRegistrationFactory
    registration_admin = 'periodicregistration'
    info_admin = 'periodicparticipant'


class PeriodicAdoptedReviewAdminTestCase(PeriodicReviewAdmin, ReviewAdminTestCase, BluebottleAdminTestCase):
    # No participant is created on the consumer, so there is no participant page to check
    pass


class PeriodicLocalReviewAdminTestCase(
    PeriodicReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    adopted = False


class DateReviewAdmin:
    activity_factory = DateActivityFactory
    registration_factory = DateRegistrationFactory
    registration_admin = 'dateregistration'
    info_admin = 'dateparticipant'

    @property
    def activity_kwargs(self):
        return {'slots': []}

    def setup_activity(self):
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            is_online=True,
            location=None,
        )

    def create_pending_registration(self):
        registration = super().create_pending_registration()
        DateParticipantFactory.create(
            activity=self.activity,
            slot=self.slot,
            registration=registration,
            user=registration.user,
            as_user=registration.user,
        )
        return registration


class DateAdoptedReviewAdminTestCase(
    DateReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    pass


class DateLocalReviewAdminTestCase(
    DateReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    adopted = False


class TeamReviewAdmin:
    activity_factory = ScheduleActivityFactory
    registration_factory = TeamScheduleRegistrationFactory
    registration_admin = 'teamscheduleregistration'
    info_admin = 'team'

    @property
    def activity_kwargs(self):
        return {'team_activity': 'teams'}

    def create_pending_registration(self):
        registration = super().create_pending_registration()
        self.team = TeamFactory.create(
            registration=registration,
            activity=self.activity,
            user=registration.user,
        )
        return registration

    @property
    def info_object(self):
        return self.team


class TeamAdoptedReviewAdminTestCase(
    TeamReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    pass


class TeamLocalReviewAdminTestCase(
    TeamReviewAdmin, RegistrationInfoTests, ReviewAdminTestCase, BluebottleAdminTestCase
):
    adopted = False
