import json
from datetime import date, timedelta

from django.core import mail
from django.urls import reverse
from rest_framework import status

from bluebottle.activities.messages.participant import InactiveParticipantAddedNotification
from bluebottle.collect.messages import ParticipantJoinedNotification as CollectJoinedNotification
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.messages import ParticipantJoinedNotification as DeedJoinedNotification
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.notifications.activity_messages import get_message_action
from bluebottle.notifications.models import ActivityMessageTemplate, MessageTemplate
from bluebottle.notifications.serializers import ActivityMessageTemplateSerializer
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import (
    APITestCase,
    BluebottleAdminTestCase,
    BluebottleTestCase,
    JSONAPITestClient,
)
from bluebottle.time_based.messages import (
    ParticipantAddedNotification,
    ParticipantSlotParticipantRegisteredNotification,
    TeamAddedNotification,
)
from bluebottle.time_based.messages.registrations import (
    DateUserAppliedNotification,
    PeriodicUserJoinedNotification,
    ScheduleUserJoinedNotification,
    TeamJoinedNotification,
    UserRegistrationAcceptedNotification,
    UserRegistrationRejectedNotification,
    UserTeamRegistrationAcceptedNotification,
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineRegistrationFactory,
    PeriodicActivityFactory,
    PeriodicRegistrationFactory,
    RegisteredDateActivityFactory,
    ScheduleActivityFactory,
    TeamScheduleRegistrationFactory,
)

ACCEPTED = 'bluebottle.time_based.messages.registrations.UserRegistrationAcceptedNotification'


def create_template(activity, action='accept', **kwargs):
    defaults = {
        'subject': 'Welcome to {title}',
        'body_html': json.dumps({'html': '<p>Hi {first_name}, see you soon!</p>', 'delta': ''}),
        'insert_method': 'replace',
    }
    defaults.update(kwargs)
    return ActivityMessageTemplate.objects.create(activity=activity, action=action, **defaults)


class ActivityMessageTemplateListAPITestCase(APITestCase):
    serializer = ActivityMessageTemplateSerializer

    def setUp(self):
        super().setUp()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeadlineActivityFactory.create(owner=self.owner)
        self.url = reverse('activity-message-template-list')

    def get_data(self, activity=None, **attributes):
        activity = activity or self.activity
        data = {
            'action': 'accept',
            'body': '<p>Hi, great to have you.</p>',
        }
        data.update(attributes)
        return {
            'data': {
                'type': 'activity-message-templates',
                'attributes': data,
                'relationships': {
                    'activity': {
                        'data': {'type': activity.JSONAPIMeta.resource_name, 'id': activity.pk}
                    }
                }
            }
        }

    def test_create_owner(self):
        self.perform_create(user=self.owner, data=self.get_data())
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, self.activity)
        self.assertEqual(self.model.action, 'accept')
        self.assertEqual(self.model.body_html.html, '<p>Hi, great to have you.</p>')
        self.assertTrue(self.response.json()['data']['meta']['permissions']['PATCH'])

    def test_create_activity_manager(self):
        manager = BlueBottleUserFactory.create()
        self.activity.initiative.activity_managers.add(manager)
        self.perform_create(user=manager, data=self.get_data())
        self.assertStatus(status.HTTP_201_CREATED)

    def test_create_other_user(self):
        self.perform_create(user=BlueBottleUserFactory.create(), data=self.get_data())
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_create_anonymous(self):
        self.perform_create(data=self.get_data())
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_create_duplicate(self):
        create_template(self.activity)
        self.perform_create(user=self.owner, data=self.get_data())
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_unsupported_activity_type(self):
        activity = RegisteredDateActivityFactory.create(owner=self.owner)
        self.perform_create(user=self.owner, data=self.get_data(activity=activity))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_action(self):
        self.perform_create(user=self.owner, data=self.get_data(action='unknown'))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_deed_join(self):
        deed = DeedFactory.create(owner=self.owner)
        self.perform_create(user=self.owner, data=self.get_data(activity=deed, action='join'))
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, deed)

    def test_create_deed_accept(self):
        deed = DeedFactory.create(owner=self.owner)
        self.perform_create(user=self.owner, data=self.get_data(activity=deed, action='accept'))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_collect_join(self):
        collect = CollectActivityFactory.create(owner=self.owner)
        self.perform_create(user=self.owner, data=self.get_data(activity=collect, action='join'))
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, collect)

    def test_list(self):
        create_template(self.activity)
        create_template(self.activity, action='reject')
        create_template(DeadlineActivityFactory.create())

        self.perform_get(user=self.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(2)

    def test_list_activity_type(self):
        create_template(self.activity)
        self.perform_get(user=self.owner)
        self.assertEqual(
            self.response.json()['data'][0]['relationships']['activity']['data'],
            {'type': 'activities/time-based/deadlines', 'id': str(self.activity.pk)}
        )

    def test_list_filter_activity(self):
        create_template(self.activity)
        create_template(DeadlineActivityFactory.create(owner=self.owner))

        self.perform_get(user=self.owner, query={'filter[activity]': self.activity.pk})
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(1)

    def test_list_other_user(self):
        create_template(self.activity)
        self.perform_get(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(0)


class RelatedActivityMessageTemplateListAPITestCase(APITestCase):
    serializer = ActivityMessageTemplateSerializer

    def setUp(self):
        super().setUp()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeadlineActivityFactory.create(owner=self.owner)
        create_template(self.activity)
        create_template(self.activity, action='join')
        create_template(DeadlineActivityFactory.create(owner=self.owner))
        self.url = reverse('deadline-message-templates', args=(self.activity.pk,))

    def test_get_owner(self):
        self.perform_get(user=self.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(2)

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(0)


class ActivityMessageTemplateDetailAPITestCase(APITestCase):
    serializer = ActivityMessageTemplateSerializer

    def setUp(self):
        super().setUp()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeadlineActivityFactory.create(owner=self.owner)
        self.model = create_template(self.activity)
        self.url = reverse('activity-message-template-detail', args=(self.model.pk,))

    def patch(self, user, **attributes):
        data = {
            'data': {
                'type': 'activity-message-templates',
                'id': self.model.pk,
                'attributes': attributes,
            }
        }
        self.response = self.client.patch(
            self.url,
            json.dumps(data),
            HTTP_AUTHORIZATION='JWT {0}'.format(user.get_jwt_token())
        )

    def test_get_owner(self):
        self.perform_get(user=self.owner)
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('body', '<p>Hi {first_name}, see you soon!</p>')

    def test_get_activity_type(self):
        self.perform_get(user=self.owner)
        self.assertEqual(
            self.response.json()['data']['relationships']['activity']['data']['type'],
            'activities/time-based/deadlines'
        )

    def test_get_other_user(self):
        self.perform_get(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_update_owner(self):
        self.patch(self.owner, body='<p>Changed</p>')
        self.assertStatus(status.HTTP_200_OK)
        self.model.refresh_from_db()
        self.assertEqual(self.model.body_html.html, '<p>Changed</p>')

    def test_update_other_user(self):
        self.patch(BlueBottleUserFactory.create(), body='<p>Changed</p>')
        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_delete_owner(self):
        self.perform_delete(user=self.owner)
        self.assertStatus(status.HTTP_204_NO_CONTENT)
        self.assertFalse(ActivityMessageTemplate.objects.filter(pk=self.model.pk).exists())

    def test_delete_other_user(self):
        self.perform_delete(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_404_NOT_FOUND)
        self.assertTrue(ActivityMessageTemplate.objects.filter(pk=self.model.pk).exists())


class ActivityMessageTemplateSendTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(activity_types=['deadlineactivity'])
        self.owner = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity = DeadlineActivityFactory.create(
            initiative=self.initiative,
            owner=self.owner,
            review=True,
            capacity=4,
            registration_deadline=None,
        )
        self.activity.states.publish(save=True)
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def register(self, activity=None):
        registration = DeadlineRegistrationFactory.create(
            activity=activity or self.activity, user=self.user, as_user=self.user
        )
        mail.outbox = []
        return registration

    def user_mails(self):
        return [m for m in mail.outbox if m.to == [self.user.email]]

    def test_accepted(self):
        create_template(self.activity)
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertEqual(message.subject, 'Welcome to {}'.format(self.activity.title))
        self.assertIn('Hi Henk, see you soon!', message.body)

    def test_rejected(self):
        create_template(self.activity, action='reject', subject='Sorry, {title} is full')
        registration = self.register()
        registration.states.reject(save=True)

        self.assertEqual(
            self.user_mails()[0].subject, 'Sorry, {} is full'.format(self.activity.title)
        )

    def test_joined(self):
        self.activity.review = False
        self.activity.save()
        create_template(self.activity, action='join', subject='Joined {title}')
        mail.outbox = []
        DeadlineRegistrationFactory.create(activity=self.activity, user=self.user, as_user=self.user)

        self.assertEqual(
            self.user_mails()[0].subject, 'Joined {}'.format(self.activity.title)
        )

    def test_applied(self):
        create_template(self.activity, action='apply', subject='Applied for {title}')
        mail.outbox = []
        DeadlineRegistrationFactory.create(activity=self.activity, user=self.user, as_user=self.user)

        self.assertEqual(
            self.user_mails()[0].subject, 'Applied for {}'.format(self.activity.title)
        )

    def test_other_activity_not_affected(self):
        create_template(DeadlineActivityFactory.create())
        registration = self.register()
        registration.states.accept(save=True)

        self.assertEqual(
            self.user_mails()[0].subject,
            'You have been selected for the activity "{}"'.format(self.activity.title)
        )

    def test_activity_template_beats_global_template(self):
        global_template = MessageTemplate.objects.create(message=ACCEPTED)
        global_template.set_current_language('en')
        global_template.subject = 'Global subject'
        global_template.body_html = json.dumps({'html': '<p>Global</p>', 'delta': ''})
        global_template.save()

        create_template(self.activity)
        registration = self.register()
        registration.states.accept(save=True)

        self.assertEqual(self.user_mails()[0].subject, 'Welcome to {}'.format(self.activity.title))

    def test_append(self):
        create_template(self.activity, insert_method='append')
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertIn('Hi Henk, see you soon!', message.body)
        self.assertIn('Good news, you have been accepted', message.body)

    def test_empty_subject_keeps_default_subject(self):
        create_template(self.activity, subject='', insert_method='append')
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertEqual(
            message.subject,
            'You have been selected for the activity "{}"'.format(self.activity.title)
        )
        self.assertIn('Hi Henk, see you soon!', message.body)

    def test_broken_template_falls_back_to_default(self):
        create_template(self.activity, subject='Hi {title')
        registration = self.register()
        registration.states.accept(save=True)

        self.assertEqual(
            self.user_mails()[0].subject,
            'You have been selected for the activity "{}"'.format(self.activity.title)
        )


class DeedCollectMessageTemplateSendTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def test_deed_joined(self):
        participant = DeedParticipantFactory.create(user=self.user)
        create_template(participant.activity, action='join', subject='Deed {title}')
        mail.outbox = []

        DeedJoinedNotification(participant).compose_and_send()

        self.assertEqual(mail.outbox[0].subject, 'Deed {}'.format(participant.activity.title))
        self.assertIn('Hi Henk, see you soon!', mail.outbox[0].body)

    def test_collect_joined(self):
        contributor = CollectContributorFactory.create(user=self.user)
        create_template(contributor.activity, action='join', subject='Collect {title}')
        mail.outbox = []

        CollectJoinedNotification(contributor).compose_and_send()

        self.assertEqual(mail.outbox[0].subject, 'Collect {}'.format(contributor.activity.title))

    def test_deed_template_not_used_for_collect(self):
        contributor = CollectContributorFactory.create(user=self.user)
        create_template(DeedFactory.create(), action='join', subject='Deed {title}')
        mail.outbox = []

        CollectJoinedNotification(contributor).compose_and_send()

        self.assertEqual(
            mail.outbox[0].subject,
            'You have joined the activity "{}"'.format(contributor.activity.title)
        )

    def test_missing_placeholder_renders_empty(self):
        participant = DeedParticipantFactory.create(user=self.user)
        create_template(participant.activity, action='join', subject='Deed {title}{duration}')
        mail.outbox = []

        DeedJoinedNotification(participant).compose_and_send()

        self.assertEqual(mail.outbox[0].subject, 'Deed {}'.format(participant.activity.title))


class ActivityMessageActionTestCase(BluebottleTestCase):
    def assertAction(self, activity, message_class, action):
        self.assertEqual(get_message_action(activity, message_class(None)), action)

    def test_date(self):
        activity = DateActivityFactory.create()
        self.assertAction(activity, ParticipantSlotParticipantRegisteredNotification, 'join')
        self.assertAction(activity, ParticipantAddedNotification, 'join')
        self.assertAction(activity, InactiveParticipantAddedNotification, 'join')
        self.assertAction(activity, DateUserAppliedNotification, 'apply')
        self.assertAction(activity, UserRegistrationAcceptedNotification, 'accept')
        self.assertAction(activity, UserRegistrationRejectedNotification, 'reject')

    def test_periodic(self):
        activity = PeriodicActivityFactory.create()
        self.assertAction(activity, PeriodicUserJoinedNotification, 'join')
        self.assertAction(activity, ScheduleUserJoinedNotification, None)

    def test_schedule_teams(self):
        activity = ScheduleActivityFactory.create()
        self.assertAction(activity, ScheduleUserJoinedNotification, 'join')
        self.assertAction(activity, TeamJoinedNotification, 'join')
        self.assertAction(activity, TeamAddedNotification, 'join')
        self.assertAction(activity, ParticipantAddedNotification, 'join')
        self.assertAction(activity, UserTeamRegistrationAcceptedNotification, 'accept')

    def test_deed(self):
        activity = DeedFactory.create()
        self.assertAction(activity, DeedJoinedNotification, 'join')
        self.assertAction(activity, ParticipantAddedNotification, 'join')
        self.assertAction(activity, InactiveParticipantAddedNotification, 'join')
        self.assertAction(activity, CollectJoinedNotification, None)
        self.assertAction(activity, UserRegistrationAcceptedNotification, None)

    def test_registered_date(self):
        activity = RegisteredDateActivityFactory.create()
        self.assertAction(activity, UserRegistrationAcceptedNotification, None)
        self.assertAction(activity, ParticipantAddedNotification, None)


class TimeBasedMessageTemplateSendTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def test_periodic_accepted(self):
        registration = PeriodicRegistrationFactory.create(user=self.user)
        create_template(registration.activity, subject='Periodic {title}')
        mail.outbox = []

        UserRegistrationAcceptedNotification(registration).compose_and_send()

        self.assertEqual(mail.outbox[0].subject, 'Periodic {}'.format(registration.activity.title))
        self.assertIn('Hi Henk, see you soon!', mail.outbox[0].body)

    def test_date_joined(self):
        activity = DateActivityFactory.create(slots=[])
        slot = DateActivitySlotFactory.create(activity=activity)
        registration = DateRegistrationFactory.create(activity=activity, user=self.user)
        participant = DateParticipantFactory.create(registration=registration, slot=slot)
        create_template(activity, action='join', subject='Date {title}')
        mail.outbox = []

        ParticipantSlotParticipantRegisteredNotification(participant).compose_and_send()

        self.assertEqual(mail.outbox[0].subject, 'Date {}'.format(activity.title))


class AddedParticipantMessageTemplateTestCase(BluebottleTestCase):
    custom = 'see you soon!'

    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create(first_name='Henk')
        self.deed = DeedFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            start=date.today() + timedelta(days=10),
            end=date.today() + timedelta(days=20),
        )

    def add_to_deed(self, email, send_messages=True):
        data = {
            'data': {
                'type': 'contributors/deeds/participants',
                'attributes': {'email': email, 'send-messages': send_messages},
                'relationships': {
                    'activity': {'data': {'type': 'activities/deeds', 'id': self.deed.pk}}
                }
            }
        }
        mail.outbox = []
        response = self.client.post(
            reverse('deed-participant-list'), json.dumps(data), user=self.deed.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def add_to_schedule(self, activity, email):
        data = {
            'data': {
                'type': 'contributors/time-based/schedule-participants',
                'attributes': {'email': email, 'send-messages': True},
                'relationships': {
                    'activity': {'data': {'type': 'activities/time-based/schedules', 'id': activity.pk}}
                }
            }
        }
        mail.outbox = []
        response = self.client.post(
            reverse('schedule-participant-create'), json.dumps(data), user=activity.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def mails_to(self, email):
        return [m for m in mail.outbox if m.to == [email]]

    def mail_to(self, email):
        messages = self.mails_to(email)
        self.assertEqual(len(messages), 1)
        return messages[0]

    def assertCustomMessageAppended(self, message, default_text):
        self.assertIn(default_text, message.body)
        self.assertIn(self.custom, message.body)
        self.assertLess(message.body.index(default_text), message.body.index(self.custom))

    def test_deed_added_by_manager(self):
        create_template(self.deed, action='join', subject='', insert_method='append')
        self.add_to_deed(self.user.email)

        message = self.mail_to(self.user.email)
        self.assertEqual(
            message.subject, 'You have been added to the activity "{}" 🎉'.format(self.deed.title)
        )
        self.assertCustomMessageAppended(message, 'You have been added to the activity')
        self.assertIn('Hi Henk, see you soon!', message.body)

    def test_deed_added_inactive_user(self):
        MemberPlatformSettings.objects.update_or_create(confirm_signup=True)
        create_template(self.deed, action='join', subject='', insert_method='append')
        self.add_to_deed('new@example.com')

        message = self.mail_to('new@example.com')
        self.assertCustomMessageAppended(message, 'activate your account')

    def test_deed_added_without_custom_message(self):
        self.add_to_deed(self.user.email)

        message = self.mail_to(self.user.email)
        self.assertIn('You have been added to the activity', message.body)
        self.assertNotIn(self.custom, message.body)

    def test_deed_added_without_sending_messages(self):
        create_template(self.deed, action='join', subject='', insert_method='append')
        self.add_to_deed(self.user.email, send_messages=False)

        self.assertEqual(self.mails_to(self.user.email), [])

    def test_deed_custom_message_not_used_for_other_activity(self):
        create_template(DeedFactory.create(), action='join', subject='', insert_method='append')
        self.add_to_deed(self.user.email)

        self.assertNotIn(self.custom, self.mail_to(self.user.email).body)

    def test_deed_added_replace(self):
        create_template(self.deed, action='join')
        self.add_to_deed(self.user.email)

        message = self.mail_to(self.user.email)
        self.assertEqual(message.subject, 'Welcome to {}'.format(self.deed.title))
        self.assertIn('Hi Henk, see you soon!', message.body)
        self.assertNotIn('You have been added to the activity', message.body)

    def test_deed_added_inactive_user_replace(self):
        MemberPlatformSettings.objects.update_or_create(confirm_signup=True)
        create_template(self.deed, action='join')
        self.add_to_deed('new@example.com')

        message = self.mail_to('new@example.com')
        self.assertEqual(message.subject, 'Welcome to {}'.format(self.deed.title))
        self.assertIn(self.custom, message.body)
        self.assertNotIn('activate your account', message.body)
        self.assertIn('/auth/confirm/?token=', message.body)

    def test_schedule_added_by_manager(self):
        activity = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
            start=date.today() + timedelta(days=10),
            deadline=date.today() + timedelta(days=20),
        )
        create_template(activity, action='join', subject='', insert_method='append')
        self.add_to_schedule(activity, self.user.email)

        self.assertCustomMessageAppended(
            self.mail_to(self.user.email), 'You have been added to the activity'
        )

    def test_schedule_team_added(self):
        activity = ScheduleActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
            team_activity='teams',
        )
        create_template(activity, action='join', subject='', insert_method='append')
        mail.outbox = []
        TeamScheduleRegistrationFactory.create(
            activity=activity, user=self.user, as_user=BlueBottleUserFactory.create(is_staff=True)
        )

        message = self.mail_to(self.user.email)
        self.assertEqual(
            message.subject, 'Your team was added to the activity "{}" 🎉'.format(activity.title)
        )
        self.assertCustomMessageAppended(message, 'Your team was added to the activity')


class BulkAddedParticipantMessageTemplateTestCase(BluebottleAdminTestCase):
    csrf_checks = False
    custom = 'see you soon!'

    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def bulk_add(self, obj, send_messages=True):
        url = reverse(
            'admin:{}_{}_bulk_add'.format(obj._meta.app_label, obj._meta.model_name),
            args=(obj.pk,)
        )
        page = self.app.get(url, user=self.superuser)
        form = [form for form in page.forms.values() if 'emails' in form.fields][0]
        form['emails'] = self.user.email
        form['send_messages'] = send_messages
        mail.outbox = []
        form.submit(user=self.superuser)
        return [m for m in mail.outbox if m.to == [self.user.email]]

    def assertCustomMessageAppended(self, messages):
        self.assertEqual(len(messages), 1)
        message = messages[0]
        default_text = 'You have been added to the activity'
        self.assertIn(default_text, message.body)
        self.assertIn('Hi Henk, see you soon!', message.body)
        self.assertLess(message.body.index(default_text), message.body.index(self.custom))

    def create_slot(self):
        activity = DateActivityFactory.create(slots=[], status='open')
        return DateActivitySlotFactory.create(activity=activity)

    def test_date_slot(self):
        slot = self.create_slot()
        create_template(slot.activity, action='join', subject='', insert_method='append')

        self.assertCustomMessageAppended(self.bulk_add(slot))

    def test_date_slot_without_custom_message(self):
        messages = self.bulk_add(self.create_slot())
        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertIn('You have been added to the activity', message.body)
        self.assertNotIn(self.custom, message.body)

    def test_deed(self):
        activity = DeedFactory.create(status='open')
        create_template(activity, action='join', subject='', insert_method='append')

        self.assertCustomMessageAppended(self.bulk_add(activity))

    def test_deed_without_sending_messages(self):
        activity = DeedFactory.create(status='open')
        create_template(activity, action='join', subject='', insert_method='append')

        self.assertEqual(self.bulk_add(activity, send_messages=False), [])

    def test_collect(self):
        activity = CollectActivityFactory.create(status='open')
        create_template(activity, action='join', subject='', insert_method='append')

        self.assertCustomMessageAppended(self.bulk_add(activity))

    def test_deadline(self):
        activity = DeadlineActivityFactory.create(status='open')
        create_template(activity, action='join', subject='', insert_method='append')

        self.assertCustomMessageAppended(self.bulk_add(activity))


class ActivityMessageDefaultListAPITestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.url = reverse('activity-message-default-list')

    def get(self, activity, user=None):
        return self.client.get(
            self.url, {'filter[activity]': activity.pk}, user=user or self.owner
        )

    def previews(self, response):
        return {
            item['attributes']['action']: item['attributes']
            for item in response.json()['data']
        }

    def test_deadline(self):
        activity = DeadlineActivityFactory.create(owner=self.owner, title='Clean the park')
        response = self.get(activity)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        previews = self.previews(response)
        self.assertEqual(set(previews), {'join', 'apply', 'accept', 'reject', 'succeed'})
        self.assertEqual(
            previews['succeed']['subject'], 'Thank you for participating in the activity "Clean the park"'
        )
        self.assertEqual(
            previews['accept']['subject'],
            'You have been selected for the activity "Clean the park"'
        )
        self.assertIn('Clean the park', previews['accept']['body'])
        self.assertIn('Hi [name],', previews['accept']['body'])
        self.assertNotIn('<html', previews['accept']['body'])
        self.assertEqual(previews['accept']['action-title'], 'View activity')
        self.assertEqual(previews['reject']['action-title'], 'View all activities')

    def test_deed(self):
        activity = DeedFactory.create(owner=self.owner, title='Plant a tree')
        previews = self.previews(self.get(activity))

        self.assertEqual(set(previews), {'join', 'succeed'})
        self.assertEqual(previews['join']['subject'], 'You have joined the activity "Plant a tree"')

    def test_deed_teams(self):
        activity = DeedFactory.create(owner=self.owner, title='Plant a tree', team_activity='teams')
        previews = self.previews(self.get(activity))

        self.assertEqual(previews['join']['subject'], 'You have joined the activity "Plant a tree"')

    def test_collect(self):
        previews = self.previews(self.get(CollectActivityFactory.create(owner=self.owner)))
        self.assertEqual(set(previews), {'join', 'succeed'})

    def test_date(self):
        activity = DateActivityFactory.create(owner=self.owner)
        previews = self.previews(self.get(activity))
        self.assertEqual(set(previews), {'join', 'apply', 'accept', 'reject', 'succeed'})

    def test_schedule_teams(self):
        activity = ScheduleActivityFactory.create(owner=self.owner, team_activity='teams')
        previews = self.previews(self.get(activity))
        self.assertIn('team', previews['accept']['subject'])

    def test_unsupported_type(self):
        response = self.get(RegisteredDateActivityFactory.create(owner=self.owner))
        self.assertEqual(response.json()['data'], [])

    def test_other_user(self):
        activity = DeadlineActivityFactory.create(owner=self.owner)
        response = self.get(activity, user=BlueBottleUserFactory.create())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous(self):
        activity = DeadlineActivityFactory.create(owner=self.owner)
        response = self.client.get(self.url, {'filter[activity]': activity.pk})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegistrationReviewMessageTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(activity_types=['deadlineactivity'])
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        initiative = InitiativeFactory.create(owner=self.owner)
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity = DeadlineActivityFactory.create(
            initiative=initiative, owner=self.owner, review=True, capacity=4,
            registration_deadline=None,
        )
        self.activity.states.publish(save=True)
        self.user = BlueBottleUserFactory.create(first_name='Henk')
        self.registration = DeadlineRegistrationFactory.create(
            activity=self.activity, user=self.user, as_user=self.user
        )
        mail.outbox = []

    def transition(self, name, message):
        data = {
            'data': {
                'type': 'contributors/time-based/deadline-registration-transitions',
                'attributes': {'transition': name, 'message': message, 'send-email': True},
                'relationships': {
                    'resource': {
                        'data': {
                            'type': 'contributors/time-based/deadline-registrations',
                            'id': self.registration.pk,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            reverse('deadline-registration-transitions'), json.dumps(data), user=self.owner
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return [m for m in mail.outbox if m.to == [self.user.email]][0]

    def test_accept_appends_message(self):
        message = self.transition('accept', '<p>Bring gloves</p>')

        self.assertIn('Good news, you have been accepted', message.body)
        self.assertIn('Bring gloves', message.body)
        self.assertLess(
            message.body.index('Good news'), message.body.index('Bring gloves')
        )

    def test_reject_appends_message(self):
        message = self.transition('reject', '<p>Maybe next time</p>')

        self.assertIn('Unfortunately, you have not been selected', message.body)
        self.assertIn('Maybe next time', message.body)

    def test_message_replaces_activity_template(self):
        create_template(self.activity, action='accept', subject='')
        message = self.transition('accept', '<p>Bring gloves</p>')

        self.assertIn('Bring gloves', message.body)
        self.assertNotIn('see you soon', message.body)
        self.assertEqual(
            message.subject,
            'You have been selected for the activity "{}"'.format(self.activity.title)
        )


class SendThankYouMessageAPITestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeadlineActivityFactory.create(owner=self.owner)
        self.url = reverse('deadline-detail', args=(self.activity.pk,))

    def test_default_off(self):
        response = self.client.get(self.url, user=self.owner)
        self.assertFalse(response.json()['data']['attributes']['send-thank-you-message'])

    def test_owner_enables(self):
        data = {
            'data': {
                'type': 'activities/time-based/deadlines',
                'id': self.activity.pk,
                'attributes': {'send-thank-you-message': True},
            }
        }
        response = self.client.patch(self.url, json.dumps(data), user=self.owner)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.activity.refresh_from_db()
        self.assertTrue(self.activity.send_thank_you_message)
