import logging

from django.utils.translation import ugettext as _
from django.db import connection

from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.payments.models import Payment
from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.utils import StatusDefinition


logger = logging.getLogger(__name__)


def get_payment_method(donation):
    order_payments = donation.order.order_payments.all()

    try:
        payment_method = order_payments[0].payment.method_name
    except Payment.DoesNotExist:
        # TODO: we need to properly handle the payment method
        #       name here. Pledges will end up here but the
        #       payment_method will be something like
        #       'pledgeStandard'...
        payment_method = order_payments[0].payment_method
        if 'pledge' in payment_method:
            payment_method = _('Invoiced')
    except IndexError:
        payment_method = ''

    return payment_method


def successful_donation_fundraiser_mail(instance):
    donation = instance

    # should be only when the status is success
    try:
        receiver = donation.fundraiser.owner
    except:
        # donation it's not coming from a fundraiser
        return

    fundraiser_link = '/go/fundraisers/{0}'.format(instance.fundraiser.id)
    pledged = (donation.order.status == StatusDefinition.PLEDGED)

    with TenantLanguage(receiver.primary_language):
        subject = _('You received a new donation')

        if instance.fundraiser.owner.email:

            if instance.anonymous:
                donor_name = _('an anonymous person')
            elif instance.order.user:
                if instance.order.user.first_name:
                    donor_name = instance.order.user.first_name
                else:
                    donor_name = instance.order.user.email
            else:
                donor_name = _('a guest')

    send_mail(
        template_name='donations/mails/new_oneoff_donation_fundraiser.mail',
        subject=subject,
        site=tenant_url(),
        to=receiver,
        link=fundraiser_link,
        donation=donation,
        pledged=pledged,
        donor_name=donor_name
    )


def new_oneoff_donation(instance):
    """
    Send project owner a mail if a new "one off" donation is done.
    We consider a donation done if the status is pending.
    """
    donation = instance

    # Only process "one-off" type donations
    if donation.order.order_type != "one-off":
        return

    project_url = '/projects/{0}'.format(donation.project.slug)
    pledged = (donation.order.status == StatusDefinition.PLEDGED)

    # Setup tenant properties for accessing tenant admin email
    if not properties.tenant_properties and connection.tenant:
        properties.set_tenant(connection.tenant)

    try:
        admin_email = properties.TENANT_MAIL_PROPERTIES.get('address')
    except AttributeError:
        logger.critical('No mail properties found for {0}'.format(connection.tenant.client_name))

    if donation.project.owner.email:
        receiver = donation.project.owner

        with TenantLanguage(receiver.primary_language):
            subject = _('You received a new donation')

            if donation.anonymous:
                donor_name = _('an anonymous person')
            elif donation.order.user:
                donor_name = donation.order.user.first_name
            else:
                donor_name = _('a guest')

        payment_method = get_payment_method(donation)

        # Send email to the project owner.
        send_mail(
            template_name='donations/mails/new_oneoff_donation.mail',
            subject=subject,
            to=receiver,
            link=project_url,
            donor_name=donor_name,
            donation=donation,
            pledged=pledged,
            admin_email=admin_email,
            payment_method=payment_method
        )

    if donation.order.user and donation.order.user.email:
        # Send email to the project supporter
        donor = donation.order.user

        with TenantLanguage(donor.primary_language):
            subject = _('Thanks for your donation')

        payment_method = get_payment_method(donation)

        send_mail(
            template_name="donations/mails/confirmation.mail",
            subject=subject,
            to=donor,
            link=project_url,
            donation=donation,
            pledged=pledged,
            payment_method=payment_method
        )
