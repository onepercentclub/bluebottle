import logging
from bunch import bunchify

from django.db import connection
from django.utils.translation import ugettext as _

from tenant_extras.utils import TenantLanguage

from bluebottle.utils.email_backend import send_mail
from bluebottle.clients import properties
from bluebottle.donations.donationmail import get_payment_method

logger = logging.getLogger(__name__)


def mail_pledge_platform_admin(donation):
    # Only process "one-off" type donations
    if donation.order.order_type != "one-off":
        return

    project_url = '/projects/{0}'.format(donation.project.slug)

    try:
        admin_email = properties.TENANT_MAIL_PROPERTIES.get('address')
    except AttributeError:
        logger.critical('No mail properties found for {0}'.format(connection.tenant.client_name))

    if admin_email:
        # Use the platform default language
        with TenantLanguage(properties.LANGUAGE_CODE):
            subject = _('A new pledge donation has been received')

        payment_method = get_payment_method(donation)

        # Create fake user object for mail
        receiver = bunchify({'email': admin_email})

        # Send email to the project owner.
        send_mail(
            template_name='payments_pledge/mails/pledge_details.mail',
            subject=subject,
            to=receiver,
            link=project_url,
            donation=donation,
            pledged=True,
            payment_method=payment_method
        )
