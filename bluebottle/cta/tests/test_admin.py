from datetime import timedelta
from unittest import mock

from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from bluebottle.cta.models import ActionDismissal
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class ActionDismissalAdminTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.member = BlueBottleUserFactory.create()
        self.ignored = ActionDismissal.objects.create(
            user=self.member, action_type='waiting_list', object_id=1
        )
        self.snoozed = ActionDismissal.objects.create(
            user=self.member,
            action_type='needs_work',
            object_id=2,
            snoozed_until=timezone.now() + timedelta(days=2),
        )
        self.changelist = reverse('admin:cta_actiondismissal_changelist')

    def rows(self, response):
        return [
            row.select_one('td.field-action_type').get_text(strip=True)
            for row in response.html.select('#result_list tbody tr')
        ]

    def test_menu_entry(self):
        response = self.app.get(reverse('admin:index'), user=self.superuser)
        self.assertContains(response, 'Dismissed actions')

    def test_changelist(self):
        response = self.app.get(self.changelist, user=self.superuser)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'waiting_list')
        self.assertContains(response, 'Current actions for a user')

    def test_filter_snoozed(self):
        response = self.app.get(self.changelist + '?status=snoozed', user=self.superuser)
        self.assertEqual(self.rows(response), ['needs_work'])

    def test_filter_ignored(self):
        response = self.app.get(self.changelist + '?status=ignored', user=self.superuser)
        self.assertEqual(self.rows(response), ['waiting_list'])

    def test_restore_action(self):
        model_admin = admin.site._registry[ActionDismissal]
        request = RequestFactory().post(self.changelist)
        request.user = self.superuser

        with mock.patch.object(model_admin, 'message_user') as message_user:
            model_admin.restore(request, ActionDismissal.objects.filter(pk=self.ignored.pk))

        message_user.assert_called_once()
        self.assertFalse(ActionDismissal.objects.filter(pk=self.ignored.pk).exists())
        self.assertTrue(ActionDismissal.objects.filter(pk=self.snoozed.pk).exists())

    def test_user_actions_page(self):
        url = reverse('admin:cta_actiondismissal_user_actions')
        response = self.app.get(url, user=self.superuser)
        self.assertEqual(response.status_code, 200)

        response = self.app.get(url + '?user={}'.format(self.member.pk), user=self.superuser)
        self.assertContains(response, self.member.email)
        self.assertContains(response, 'This member has no actions.')

    def test_user_actions_page_unknown_member(self):
        url = reverse('admin:cta_actiondismissal_user_actions')
        response = self.app.get(url + '?user=99999999', user=self.superuser)
        self.assertContains(response, 'No member found with that id.')
