# -*- coding: utf-8 -*-
from django.urls import reverse

from bluebottle.notifications.models import MessageTemplate
from bluebottle.test.utils import BluebottleAdminTestCase


class TestMessageTemplateAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestMessageTemplateAdmin, self).setUp()
        self.client.force_login(self.superuser)

    def test_new_mail_template_admin(self):
        self.admin_url = reverse('admin:notifications_messagetemplate_add')
        response = self.client.get(self.admin_url)
        self.assertNotContains(response, 'Body')
        self.assertNotContains(response, '{first_name}')

    def test_mail_template_admin(self):
        template = MessageTemplate.objects.create(
            message='bluebottle.members.messages.AccoutnActivationMessage'
        )
        self.admin_url = reverse('admin:notifications_messagetemplate_change', args=(template.id,))
        response = self.client.get(self.admin_url)
        # Check we show placeholder hints
        self.assertContains(response, '{first_name}')
        self.assertContains(response, '{site_name}')
        self.assertContains(response, 'Body')
