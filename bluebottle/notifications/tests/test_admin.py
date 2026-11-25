# -*- coding: utf-8 -*-
import json

from django.urls import reverse

from bluebottle.collect.tests.factories import CollectActivityFactory
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.notifications.models import ActivityMessageTemplate, MessageTemplate
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DeadlineActivityFactory


class TestMessageTemplateAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestMessageTemplateAdmin, self).setUp()
        self.client.force_login(self.superuser)

    def test_new_mail_template_admin(self):
        self.admin_url = reverse('admin:notifications_messagetemplate_add')
        response = self.client.get(self.admin_url)
        self.assertNotContains(response, '{first_name}')

    def test_mail_template_admin(self):
        template = MessageTemplate.objects.create(
            message='bluebottle.members.messages.AccountActivationMessage'
        )
        self.admin_url = reverse('admin:notifications_messagetemplate_change', args=(template.id,))
        response = self.client.get(self.admin_url)

        # Check we show placeholder hints
        self.assertContains(response, '{first_name}')
        self.assertContains(response, '{site_name}')


class ActivityMessageTemplateAdminInlineTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.superuser)

    def get_form(self, activity):
        url = reverse(
            f'admin:{activity._meta.app_label}_{activity._meta.model_name}_change',
            args=(activity.pk,)
        )
        return self.app.get(url).forms[f'{activity._meta.model_name}_form']

    def action_choices(self, form, index='__prefix__'):
        return [value for value, _, _ in form[f'message_templates-{index}-action'].options if value]

    def test_deed_actions(self):
        form = self.get_form(DeedFactory.create())
        self.assertEqual(self.action_choices(form), ['join', 'succeed'])

    def test_collect_actions(self):
        form = self.get_form(CollectActivityFactory.create())
        self.assertEqual(self.action_choices(form), ['join', 'succeed'])

    def test_date_without_review_actions(self):
        form = self.get_form(DateActivityFactory.create(review=False))
        self.assertEqual(self.action_choices(form), ['join', 'succeed'])

    def test_date_with_review_actions(self):
        form = self.get_form(DateActivityFactory.create(review=True))
        self.assertEqual(self.action_choices(form), ['accept', 'reject', 'succeed'])

    def test_existing_unavailable_action_is_kept(self):
        activity = DeadlineActivityFactory.create(review=False)
        ActivityMessageTemplate.objects.create(activity=activity, action='accept')
        form = self.get_form(activity)
        self.assertEqual(self.action_choices(form, 0), ['join', 'succeed', 'accept'])
        self.assertEqual(self.action_choices(form), ['join', 'succeed'])

    def test_add_activity_page(self):
        form = self.app.get(reverse('admin:deeds_deed_add')).forms['deed_form']
        self.assertEqual(self.action_choices(form), [])

    def add_template(self, activity, action):
        form = self.get_form(activity)
        self.admin_add_inline_form_entry(form, 'message_templates')
        form['message_templates-0-action'] = action
        form['message_templates-0-body_html'] = json.dumps({'html': '<p>Hi</p>', 'delta': ''})
        return form.submit()

    def test_add_valid_action(self):
        activity = CollectActivityFactory.create()
        page = self.add_template(activity, 'join')
        if 'confirm' in page.forms:
            page.forms['confirm'].submit()
        self.assertEqual(
            list(activity.message_templates.values_list('action', flat=True)), ['join']
        )

    def test_add_invalid_action(self):
        activity = CollectActivityFactory.create()
        page = self.add_template(activity, 'accept')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Select a valid choice', page.text)
        self.assertFalse(activity.message_templates.exists())
