import json

from django.core import mail
from django.urls import reverse
from rest_framework import status

from bluebottle.collect.messages import ParticipantJoinedNotification as CollectJoinedNotification
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.messages import ParticipantJoinedNotification as DeedJoinedNotification
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.initiatives.tests.factories import (
    InitiativeFactory,
    InitiativePlatformSettingsFactory,
)
from bluebottle.notifications.models import ActivityMessageTemplate, MessageTemplate
from bluebottle.notifications.serializers import ActivityMessageTemplateSerializer
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase, BluebottleTestCase
from bluebottle.notifications.activity_messages import get_message_action
from bluebottle.time_based.messages import ParticipantSlotParticipantRegisteredNotification
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
            'subject': 'You are in for {title}!',
            'body': '<p>Hi {first_name}, great to have you.</p>',
            'insert-method': 'replace',
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

    def test_create_without_subject(self):
        data = self.get_data()
        del data['data']['attributes']['subject']
        self.perform_create(user=self.owner, data=data)
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.subject, '')

    def test_create_owner(self):
        self.perform_create(user=self.owner, data=self.get_data())
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, self.activity)
        self.assertEqual(self.model.action, 'accept')
        self.assertEqual(self.model.subject, 'You are in for {title}!')
        self.assertEqual(self.model.body_html.html, '<p>Hi {first_name}, great to have you.</p>')
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
        self.perform_create(user=self.owner, data=self.get_data(action='succeed'))
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

    def test_create_unknown_placeholder(self):
        self.perform_create(user=self.owner, data=self.get_data(subject='Hi {password}'))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_attribute_placeholder(self):
        self.perform_create(
            user=self.owner,
            data=self.get_data(body='<p>{title.__class__.__init__}</p>')
        )
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_broken_braces(self):
        self.perform_create(user=self.owner, data=self.get_data(subject='Hi {title'))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

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
        self.assertAttribute('subject', 'Welcome to {title}')
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
        self.patch(self.owner, subject='Changed {title}')
        self.assertStatus(status.HTTP_200_OK)
        self.model.refresh_from_db()
        self.assertEqual(self.model.subject, 'Changed {title}')

    def test_update_other_user(self):
        self.patch(BlueBottleUserFactory.create(), subject='Changed')
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
        self.assertAction(activity, UserTeamRegistrationAcceptedNotification, 'accept')

    def test_deed(self):
        activity = DeedFactory.create()
        self.assertAction(activity, DeedJoinedNotification, 'join')
        self.assertAction(activity, CollectJoinedNotification, None)
        self.assertAction(activity, UserRegistrationAcceptedNotification, None)

    def test_registered_date(self):
        activity = RegisteredDateActivityFactory.create()
        self.assertAction(activity, UserRegistrationAcceptedNotification, None)


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
