from babel.dates import format_date
from babel.numbers import format_currency
from bluebottle.clients.context import ClientContext
from bluebottle.clients.mail import EmailMultiAlternatives
from bluebottle.clients.utils import tenant_url
from celery import task
from django.template.loader import get_template


@task
def mail_monthly_donation_processed_notification(monthly_order):
    # TODO: Use English base and the regular translation mechanism.
    receiver = monthly_order.user

    context = ClientContext(
                       {'order': monthly_order,
                       'receiver_first_name': receiver.first_name.capitalize(),
                       'date': format_date(locale='nl_NL'),
                       'amount': format_currency(monthly_order.amount, 'EUR', locale='nl_NL'),
                       'site': tenant_url()})

    subject = "Bedankt voor je maandelijkse support"
    text_content = get_template('monthly_donation.nl.mail.txt').render(context)
    html_content = get_template('monthly_donation.nl.mail.html').render(context)
    msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@task
def mail_project_funded_monthly_donor_notification(receiver, project):
    # TODO: Use English base and the regular translation mechanism.
    context = ClientContext(
                      {'receiver_first_name': receiver.first_name.capitalize(),
                       'project': project,
                       'link': '/go/projects/{0}'.format(project.slug),
                       'site': tenant_url()})

    subject = "Gefeliciteerd: project afgerond!"
    text_content = get_template('project_full_monthly_donor.nl.mail.txt').render(context)
    html_content = get_template('project_full_monthly_donor.nl.mail.html').render(context)
    msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[receiver.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
