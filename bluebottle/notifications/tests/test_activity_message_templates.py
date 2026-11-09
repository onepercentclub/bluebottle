import json

from django.contrib.auth.models import Group
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
from bluebottle.notifications.activity_messages import get_message_action
from bluebottle.notifications.models import ActivityMessageTemplate, MessageTemplate
from bluebottle.notifications.serializers import ActivityMessageTemplateSerializer
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase, BluebottleTestCase, JSONAPITestClient
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


def create_staff_user():
    user = BlueBottleUserFactory.create(is_staff=True)
    user.groups.add(Group.objects.get(name='Staff'))
    return user


def create_template(activity, action='accept', **kwargs):
    defaults = {
        'body_html': json.dumps({'html': '<p>Hi there, see you soon!</p>', 'delta': ''}),
        'insert_method': 'replace',
    }
    defaults.update(kwargs)
    return ActivityMessageTemplate.objects.create(activity=activity, action=action, **defaults)


class ActivityMessageTemplateListAPITestCase(APITestCase):
    serializer = ActivityMessageTemplateSerializer

    def setUp(self):
        super().setUp()
        self.owner = BlueBottleUserFactory.create()
        self.activity = DeadlineActivityFactory.create(owner=self.owner, review=True)
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

    def test_create_staff(self):
        self.perform_create(user=create_staff_user(), data=self.get_data())
        self.assertStatus(status.HTTP_201_CREATED)
        self.assertEqual(self.model.activity, self.activity)

    def test_create_superuser(self):
        self.perform_create(user=BlueBottleUserFactory.create(is_superuser=True), data=self.get_data())
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

    def test_create_apply(self):
        self.perform_create(user=self.owner, data=self.get_data(action='apply'))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_join_with_review(self):
        self.perform_create(user=self.owner, data=self.get_data(action='join'))
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_join_without_review(self):
        activity = DeadlineActivityFactory.create(owner=self.owner, review=False)
        self.perform_create(user=self.owner, data=self.get_data(activity=activity, action='join'))
        self.assertStatus(status.HTTP_201_CREATED)

    def test_create_accept_without_review(self):
        activity = DeadlineActivityFactory.create(owner=self.owner, review=False)
        self.perform_create(user=self.owner, data=self.get_data(activity=activity, action='accept'))
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
        self.activity = DeadlineActivityFactory.create(owner=self.owner, review=True)
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
        self.assertAttribute('body', '<p>Hi there, see you soon!</p>')

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

    def test_update_staff(self):
        self.patch(create_staff_user(), body='<p>Changed</p>')
        self.assertStatus(status.HTTP_200_OK)
        self.model.refresh_from_db()
        self.assertEqual(self.model.body_html.html, '<p>Changed</p>')

    def test_update_superuser(self):
        self.patch(BlueBottleUserFactory.create(is_superuser=True), body='<p>Changed</p>')
        self.assertStatus(status.HTTP_200_OK)

    def test_update_other_user(self):
        self.patch(BlueBottleUserFactory.create(), body='<p>Changed</p>')
        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_update_anonymous(self):
        self.response = self.client.patch(self.url, json.dumps({}))
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_delete_staff(self):
        self.perform_delete(user=create_staff_user())
        self.assertStatus(status.HTTP_204_NO_CONTENT)

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

    def assertDefaultSubject(self, message):
        self.assertEqual(
            message.subject,
            'You have been selected for the activity "{}"'.format(self.activity.title)
        )

    def test_accepted(self):
        create_template(self.activity)
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertDefaultSubject(message)
        self.assertIn('Hi there, see you soon!', message.body)
        self.assertNotIn('Good news, you have been accepted', message.body)

    def test_rejected(self):
        create_template(self.activity, action='reject')
        registration = self.register()
        registration.states.reject(save=True)

        self.assertIn('Hi there, see you soon!', self.user_mails()[0].body)

    def test_joined(self):
        self.activity.review = False
        self.activity.save()
        create_template(self.activity, action='join')
        mail.outbox = []
        DeadlineRegistrationFactory.create(activity=self.activity, user=self.user, as_user=self.user)

        self.assertIn('Hi there, see you soon!', self.user_mails()[0].body)

    def test_applied(self):
        create_template(self.activity, action='apply')
        mail.outbox = []
        DeadlineRegistrationFactory.create(activity=self.activity, user=self.user, as_user=self.user)

        self.assertIn('Hi there, see you soon!', self.user_mails()[0].body)

    def test_other_activity_not_affected(self):
        create_template(DeadlineActivityFactory.create())
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertDefaultSubject(message)
        self.assertNotIn('Hi there, see you soon!', message.body)

    def test_activity_template_beats_global_template(self):
        global_template = MessageTemplate.objects.create(message=ACCEPTED)
        global_template.set_current_language('en')
        global_template.subject = 'Global subject'
        global_template.body_html = json.dumps({'html': '<p>Global</p>', 'delta': ''})
        global_template.save()

        create_template(self.activity)
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertDefaultSubject(message)
        self.assertIn('Hi there, see you soon!', message.body)
        self.assertNotIn('Global', message.body)

    def test_global_template_placeholders(self):
        global_template = MessageTemplate.objects.create(message=ACCEPTED)
        global_template.set_current_language('en')
        global_template.subject = 'Welcome to {title}'
        global_template.body_html = json.dumps({'html': '<p>Hi {first_name}</p>', 'delta': ''})
        global_template.save()

        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertEqual(message.subject, 'Welcome to {}'.format(self.activity.title))
        self.assertIn('Hi Henk', message.body)

    def test_append(self):
        create_template(self.activity, insert_method='append')
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertIn('Hi there, see you soon!', message.body)
        self.assertIn('Good news, you have been accepted', message.body)

    def test_template_subject_is_ignored(self):
        create_template(self.activity, subject='Custom {title}')
        registration = self.register()
        registration.states.accept(save=True)

        self.assertDefaultSubject(self.user_mails()[0])

    def test_placeholders_are_sent_literally(self):
        create_template(
            self.activity,
            body_html=json.dumps({'html': '<p>Hello {title} {recipient_name}</p>', 'delta': ''})
        )
        registration = self.register()
        registration.states.accept(save=True)

        self.assertIn('Hello {title} {recipient_name}', self.user_mails()[0].body)

    def test_lone_brace_is_sent_literally(self):
        create_template(
            self.activity,
            insert_method='append',
            body_html=json.dumps({'html': '<p>a { b</p>', 'delta': ''})
        )
        registration = self.register()
        registration.states.accept(save=True)

        message = self.user_mails()[0]
        self.assertIn('a { b', message.body)
        self.assertIn('Good news, you have been accepted', message.body)

    def test_message_block_html_is_literal(self):
        create_template(
            self.activity,
            body_html=json.dumps({'html': '<p>a { b {title}</p>', 'delta': ''})
        )
        registration = self.register()

        self.assertEqual(
            UserRegistrationAcceptedNotification(registration).get_message_block_html(self.user),
            '<p>a { b {title}</p>'
        )


class DeedCollectMessageTemplateSendTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def test_deed_joined(self):
        participant = DeedParticipantFactory.create(user=self.user)
        create_template(participant.activity, action='join')
        mail.outbox = []

        DeedJoinedNotification(participant).compose_and_send()

        self.assertIn('Hi there, see you soon!', mail.outbox[0].body)

    def test_collect_joined(self):
        contributor = CollectContributorFactory.create(user=self.user)
        create_template(contributor.activity, action='join')
        mail.outbox = []

        CollectJoinedNotification(contributor).compose_and_send()

        self.assertIn('Hi there, see you soon!', mail.outbox[0].body)

    def test_deed_template_not_used_for_collect(self):
        contributor = CollectContributorFactory.create(user=self.user)
        create_template(DeedFactory.create(), action='join')
        mail.outbox = []

        CollectJoinedNotification(contributor).compose_and_send()

        self.assertEqual(
            mail.outbox[0].subject,
            'You have joined the activity "{}"'.format(contributor.activity.title)
        )
        self.assertNotIn('Hi there, see you soon!', mail.outbox[0].body)


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
        create_template(registration.activity)
        mail.outbox = []

        UserRegistrationAcceptedNotification(registration).compose_and_send()

        self.assertIn('Hi there, see you soon!', mail.outbox[0].body)

    def test_date_joined(self):
        activity = DateActivityFactory.create(slots=[])
        slot = DateActivitySlotFactory.create(activity=activity)
        registration = DateRegistrationFactory.create(activity=activity, user=self.user)
        participant = DateParticipantFactory.create(registration=registration, slot=slot)
        create_template(activity, action='join')
        mail.outbox = []

        ParticipantSlotParticipantRegisteredNotification(participant).compose_and_send()

        self.assertIn('Hi there, see you soon!', mail.outbox[0].body)


class DateReviewJoinMessageTemplateTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        InitiativePlatformSettingsFactory.create(activity_types=['dateactivity'])
        self.owner = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create(owner=self.owner)
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.activity = DateActivityFactory.create(
            initiative=self.initiative,
            owner=self.owner,
            review=True,
            slots=[],
        )
        self.slots = DateActivitySlotFactory.create_batch(2, activity=self.activity)
        self.activity.states.publish(save=True)
        self.user = BlueBottleUserFactory.create(first_name='Henk')

    def join(self, slot):
        return DateParticipantFactory.create(
            activity=self.activity, slot=slot, user=self.user, registration=None, as_user=self.user
        )

    def user_mails(self):
        return [m for m in mail.outbox if m.to == [self.user.email]]

    def join_after_accept(self):
        participant = self.join(self.slots[0])
        participant.registration.states.accept(save=True)
        mail.outbox = []
        return self.join(self.slots[1])

    def test_join_uses_accept_template(self):
        create_template(self.activity, subject='', insert_method='append')
        participant = self.join_after_accept()

        self.assertEqual(participant.status, 'accepted')
        messages = self.user_mails()
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0].subject,
            'You\'ve registered for a time slot for the activity "{}"'.format(self.activity.title)
        )
        self.assertIn('You are registered for a time slot', messages[0].body)
        self.assertIn('Hi Henk, see you soon!', messages[0].body)

    def test_join_template_beats_accept_template(self):
        create_template(self.activity)
        create_template(self.activity, action='join', subject='Joined {title}')
        self.join_after_accept()

        self.assertEqual(
            self.user_mails()[0].subject, 'Joined {}'.format(self.activity.title)
        )

    def test_review_disabled_ignores_accept_template(self):
        self.activity.review = False
        self.activity.save()
        create_template(self.activity)
        mail.outbox = []
        self.join(self.slots[0])

        self.assertEqual(
            self.user_mails()[0].subject,
            'You\'ve registered for a time slot for the activity "{}"'.format(self.activity.title)
        )


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
        create_template(self.activity, action='accept')
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

    def enable(self, user):
        data = {
            'data': {
                'type': 'activities/time-based/deadlines',
                'id': self.activity.pk,
                'attributes': {'send-thank-you-message': True},
            }
        }
        response = self.client.patch(self.url, json.dumps(data), user=user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.activity.refresh_from_db()
        self.assertTrue(self.activity.send_thank_you_message)

    def test_owner_enables(self):
        self.enable(self.owner)

    def test_staff_enables(self):
        self.enable(create_staff_user())

    def test_superuser_enables(self):
        self.enable(BlueBottleUserFactory.create(is_superuser=True))
