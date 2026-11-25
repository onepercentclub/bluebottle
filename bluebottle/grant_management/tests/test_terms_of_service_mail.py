import json
from unittest import expectedFailure

from django.core import mail

from bluebottle.grant_management.tests.factories import GrantApplicationFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.notifications.models import MessageTemplate
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

BCC = 'bcc@example.com'


class BaseGrantTermsOfServiceMailTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.settings = InitiativePlatformSettings.load()
        self.settings.mail_terms_of_service = True
        self.settings.bcc_terms_of_service = BCC
        self.settings.terms_of_service = 'Default terms of service'
        self.settings.save()

    def approve(self, **kwargs):
        owner = kwargs.pop('owner', None) or BlueBottleUserFactory.create()
        application = GrantApplicationFactory.create(
            title='Save the world!', initiative=None, tos_accepted=True, owner=owner, **kwargs
        )
        application.states.submit(save=True)
        mail.outbox = []
        application.states.approve(save=True)
        return application

    def tos_mail(self):
        mails = [message for message in mail.outbox if BCC in message.bcc]
        self.assertEqual(len(mails), 1, [message.subject for message in mail.outbox])
        return mails[0]

    def assertTosInMail(self, text, message=None):
        message = message or self.tos_mail()
        html = message.alternatives[0][0]
        self.assertIn(text, html)
        self.assertIn(text, message.body)


class GrantTermsOfServiceMailTestCase(BaseGrantTermsOfServiceMailTestCase):
    """Approving a grant application should email the ToS to the applicant and the BCC address."""

    def test_applicant_receives_terms_of_service(self):
        # Delivery-agnostic: the ToS may be in the approval mail or in a separate mail.
        self.settings.terms_of_service = 'Unique applicant terms 7731'
        self.settings.save()
        application = self.approve()

        to_applicant = [m for m in mail.outbox if m.to == [application.owner.email]]
        with_html = [m for m in to_applicant if 'Unique applicant terms 7731' in m.alternatives[0][0]]
        with_text = [m for m in to_applicant if 'Unique applicant terms 7731' in m.body]
        self.assertTrue(
            with_html and with_text,
            'Applicant did not receive the terms of service. Mails to applicant: {}'.format(
                [m.subject for m in to_applicant]
            )
        )

    def test_applicant_receives_terms_when_approved_with_custom_message(self):
        # The back-office confirm form posts the edited approval text as `message`
        self.settings.terms_of_service = 'Unique applicant terms 7731'
        self.settings.save()
        owner = BlueBottleUserFactory.create()
        application = GrantApplicationFactory.create(
            title='Save the world!', initiative=None, tos_accepted=True, owner=owner
        )
        application.states.submit(save=True)
        mail.outbox = []
        application.states.approve()
        application.execute_triggers(send_messages=True, message='<p>Edited approval text 5590</p>')
        application.save()

        to_applicant = [m for m in mail.outbox if m.to == [owner.email]]
        approval = [m for m in to_applicant if 'Edited approval text 5590' in m.alternatives[0][0]]
        terms = [m for m in to_applicant if 'Unique applicant terms 7731' in m.alternatives[0][0]]
        self.assertEqual(len(approval), 1, [m.subject for m in to_applicant])
        self.assertEqual(len(terms), 1, [m.subject for m in to_applicant])
        self.assertNotIn('Unique applicant terms 7731', approval[0].alternatives[0][0])
        self.assertNotIn('Edited approval text 5590', terms[0].alternatives[0][0])
        self.assertEqual(terms[0].bcc, [BCC])

    def test_applicant_receives_custom_mail_text(self):
        self.settings.terms_of_service_mail_text = 'Unique custom mail terms 4412 for {partner_organization}'
        self.settings.save()
        application = self.approve()

        to_applicant = [m for m in mail.outbox if m.to == [application.owner.email]]
        self.assertTrue(
            any('Unique custom mail terms 4412' in m.alternatives[0][0] for m in to_applicant),
            [m.subject for m in to_applicant]
        )

    def test_mail_sent_to_applicant_and_bcc(self):
        application = self.approve()
        message = self.tos_mail()
        self.assertEqual(message.to, [application.owner.email])
        self.assertEqual(message.bcc, [BCC])
        self.assertTosInMail('Default terms of service', message)

    def test_application_with_initiative(self):
        initiative = InitiativeFactory.create(status='approved')
        application = GrantApplicationFactory.create(
            title='Save the world!', initiative=initiative, tos_accepted=True
        )
        application.states.submit(save=True)
        mail.outbox = []
        application.states.approve(save=True)
        self.assertTosInMail('Default terms of service')

    def test_multiline_terms(self):
        self.settings.terms_of_service = 'Line one\n\nLine two\nLine three'
        self.settings.save()
        self.approve()
        self.assertTosInMail('Line one')
        self.assertTosInMail('Line three')

    def test_approved_mail_does_not_contain_tos(self):
        self.approve()
        approved = [m for m in mail.outbox if BCC not in m.bcc]
        self.assertEqual(len(approved), 1)
        self.assertNotIn('Default terms of service', approved[0].body)

    def test_html_terms(self):
        self.settings.terms_of_service = (
            '<h2>Terms</h2>\n<p>Please <strong>read</strong> <a href="https://example.com/tos">this</a>.</p>\n'
            '<ul>\n<li>First rule</li>\n<li>Second rule</li>\n</ul>'
        )
        self.settings.save()
        self.approve()
        self.assertTosInMail('First rule')
        self.assertTosInMail('Second rule')
        self.assertIn('https://example.com/tos', self.tos_mail().alternatives[0][0])

    @expectedFailure
    def test_curly_braces_in_terms(self):
        self.settings.terms_of_service = 'Fines up to {EUR 500} may apply'
        self.settings.save()
        self.approve()
        self.assertTosInMail('Fines up to')

    @expectedFailure
    def test_css_in_terms(self):
        self.settings.terms_of_service = '<style>p { color: red; }</style><p>Styled terms</p>'
        self.settings.save()
        self.approve()
        self.assertTosInMail('Styled terms')

    def test_placeholders_in_terms(self):
        self.settings.terms_of_service = 'Agreed by {partner_organization} for "{title}"'
        self.settings.save()
        application = self.approve()
        self.assertTosInMail('Agreed by {} for'.format(application.owner.full_name))

    def test_special_characters_in_terms(self):
        self.settings.terms_of_service = 'Rate: 100% of the € grant – “quoted” & more < 5'
        self.settings.save()
        self.approve()
        self.assertTosInMail('100% of the')

    def test_long_terms(self):
        self.settings.terms_of_service = '\n'.join(
            'Clause number {} of the terms of service.'.format(i) for i in range(5000)
        )
        self.settings.save()
        self.approve()
        self.assertTosInMail('Clause number 4999')

    def test_custom_mail_text(self):
        self.settings.terms_of_service_mail_text = 'Mail only terms'
        self.settings.save()
        self.approve()
        self.assertTosInMail('Mail only terms')

    def test_dutch_recipient(self):
        self.approve(owner=BlueBottleUserFactory.create(primary_language='nl'))
        self.assertTosInMail('Default terms of service')

    def test_only_bcc_when_configured(self):
        self.settings.bcc_terms_of_service = ''
        self.settings.save()
        self.approve()
        mails = [m for m in mail.outbox if 'Default terms of service' in m.body]
        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].bcc, [])

    def test_not_sent_when_disabled(self):
        self.settings.mail_terms_of_service = False
        self.settings.save()
        self.approve()
        self.assertEqual([m for m in mail.outbox if 'Default terms of service' in m.body], [])


class GrantTermsOfServiceCustomTemplateTestCase(BaseGrantTermsOfServiceMailTestCase):
    """A custom message template for the ToS notification can hide the ToS."""

    def create_template(self, insert_method, body):
        template = MessageTemplate.objects.create(
            message='bluebottle.activities.messages.activity_manager.TermsOfServiceNotification',
            insert_method=insert_method
        )
        template.set_current_language('en')
        template.subject = 'Your terms'
        template.body_html = json.dumps({'html': body, 'delta': ''})
        template.save()

    def test_custom_template_append(self):
        self.create_template('append', 'Extra intro text')
        self.approve()
        self.assertTosInMail('Extra intro text')
        self.assertTosInMail('Default terms of service')

    def test_custom_template_replace_with_placeholder(self):
        self.create_template('replace', 'Replaced. {terms_of_service}')
        self.approve()
        self.assertTosInMail('Replaced.')
        self.assertTosInMail('Default terms of service')

    @expectedFailure
    def test_custom_template_replace_without_placeholder(self):
        self.create_template('replace', 'Replaced, no placeholder')
        self.approve()
        self.assertTosInMail('Default terms of service')
