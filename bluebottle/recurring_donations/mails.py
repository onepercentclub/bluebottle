from babel.dates import format_date
from babel.numbers import format_currency
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.utils.email_backend import send_mail


def mail_monthly_donation_processed_notification(monthly_order):

    receiver = monthly_order.user
    translation.activate(receiver.primary_language)

    subject = _("Thank you for your monthly support")

    send_mail(
        template_name='recurring_donations/mails/monthly_donation.mail',
        subject=subject,
        site=tenant_url(),
        to=receiver,
        order=monthly_order,
        receiver_first_name=receiver.first_name.capitalize(),
        date=format_date(locale='nl_NL'),
        amount=format_currency(monthly_order.amount, 'EUR', locale='nl_NL'),
    )


def mail_project_funded_monthly_donor_notification(receiver, project):

    cur_language = translation.get_language()

    if receiver.primary_language:
        translation.activate(receiver.primary_language)
    else:
        translation.activate(properties.LANGUAGE_CODE)

    subject = _("Congratulations: project completed!")

    translation.activate(cur_language)

    send_mail(
        template_name='recurring_donations/mails/project_full_monthly_donor.mail',
        subject=subject,
        receiver_first_name=receiver.first_name.capitalize(),
        to=receiver,
        project=project,
        link='/go/projects/{0}'.format(project.slug)
    )
