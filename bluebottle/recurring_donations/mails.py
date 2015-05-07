from babel.dates import format_date
from babel.numbers import format_currency
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.utils.email_backend import send_mail


def mail_monthly_donation_processed_notification(monthly_order):

    cur_language = translation.get_language()
    receiver = monthly_order.user
    subject = _("Thank you for your monthly support")

    translation.activate(cur_language)

    send_mail(
        template_name='recurring_donations/mails/monthly_donation.mail',
        subject=subject,
        to=receiver,
        order=monthly_order,
        receiver_first_name=receiver.first_name.capitalize(),
        link='/go/projects',
        date=format_date(locale='nl_NL'),
        amount=format_currency(monthly_order.amount, 'EUR', locale='nl_NL')
    )


def mail_project_funded_monthly_donor_notification(receiver, project):

    subject = _("Congratulations: project completed!")

    send_mail(
        template_name='recurring_donations/mails/project_full_monthly_donor.mail',
        subject=subject,
        receiver_first_name=receiver.first_name.capitalize(),
        to=receiver,
        project=project,
        link='/go/projects/{0}'.format(project.slug)
    )
