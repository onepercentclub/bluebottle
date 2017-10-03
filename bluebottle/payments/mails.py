from django.utils.translation import ugettext as _

from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.clients.utils import tenant_url
from bluebottle.utils.email_backend import send_mail


def order_payment_refund_mail(instance):
    order_payment = instance
    order = order_payment.order
    receiver = order.user

    try:
        # NOTE: only handling on order with a single donation
        donation = order.donations.first()
    except IndexError:
        return

    try:
        if donation.fundraiser:
            project = donation.fundraiser.project
        else:
            project = donation.project
    except AttributeError:
        return

    with TenantLanguage(receiver.primary_language):
        subject = _('Donation Refund')
        admin_email = properties.TENANT_MAIL_PROPERTIES.get('address')

        send_mail(
            template_name='payments/mails/order_payment_refund.mail',
            subject=subject,
            to=receiver,
            site=tenant_url(),
            project=project,
            admin_email=admin_email
        )
