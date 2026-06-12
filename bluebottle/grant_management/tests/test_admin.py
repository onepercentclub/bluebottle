from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from bluebottle.fsm.state import TRANSITION
from bluebottle.grant_management.admin import GrantApplicationAdmin
from bluebottle.grant_management.models import GrantApplication
from bluebottle.grant_management.tests.factories import GrantApplicationFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class GrantApplicationAdminTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.changelist_url = reverse('admin:grant_management_grantapplication_changelist')
        self.client.force_login(self.superuser)

    def test_changelist_renders_without_submit_log_entry(self):
        GrantApplicationFactory.create(status='draft')

        response = self.client.get(self.changelist_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_submitted_column_returns_none_without_log_entry(self):
        application = GrantApplicationFactory.create(status='draft')
        admin = GrantApplicationAdmin(GrantApplication, None)

        self.assertIsNone(admin.submitted(application))

    def test_submitted_column_returns_action_time_from_log_entry(self):
        application = GrantApplicationFactory.create(status='submitted')
        submitted_at = now()
        LogEntry.objects.create(
            user_id=self.superuser.pk,
            content_type=ContentType.objects.get_for_model(application),
            object_id=str(application.pk),
            object_repr=str(application),
            action_flag=TRANSITION,
            change_message='Changed status to submitted',
            action_time=submitted_at,
        )
        admin = GrantApplicationAdmin(GrantApplication, None)

        self.assertEqual(admin.submitted(application), submitted_at)

        response = self.client.get(self.changelist_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
