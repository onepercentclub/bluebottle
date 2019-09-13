import hashlib
import json

import requests
from django.db import connection
from django.urls import reverse

from bluebottle.funding.exception import PaymentException

from django.utils.translation import ugettext_lazy as _


def get_payment_url(payment):
    """
    Get payment url from VitePay to redirect the user to.
    """
    from bluebottle.funding_vitepay.models import VitepayPaymentProvider
    domain = connection.tenant.domain_url
    if 'localhost' in domain:
        # Use a mocked url that will always return the expected result
        domain = 'https://{}.t.goodup.com'.format(connection.tenant.client_name)

    provider = VitepayPaymentProvider.objects.get()
    credentials = provider.private_settings

    return_url = "{}/initiatives/activities/details/funding/{}/{}?donation_id={}".format(
        domain,
        payment.donation.activity.id,
        payment.donation.activity.slug,
        payment.donation.id
    )

    description = _('payment for {activity_title} on {tenant_name}').format(
        activity_title=payment.donation.activity.title,
        tenant_name=connection.tenant.name)

    api_secret = credentials['api_secret']
    amount_100 = int(payment.donation.amount.amount * 100)
    callback_url = "{}{}".format(domain, reverse('vitepay-payment-webhook'))

    message = "{order_id};{amount_100};{currency};" \
              "{callback_url};{api_secret}".format(order_id=payment.unique_id,
                                                   currency=payment.donation.amount.currency,
                                                   amount_100=amount_100,
                                                   callback_url=callback_url,
                                                   api_secret=api_secret)

    payment_hash = hashlib.sha1(message.upper()).hexdigest()

    data = {
        "payment": {
            "language_code": "fr",
            "currency_code": "XOF",
            "country_code": "ML",
            "order_id": payment.unique_id,
            "description": description,
            "amount_100": int(payment.donation.amount.amount * 100),
            "return_url": return_url,
            "decline_url": return_url,
            "cancel_url": return_url,
            "callback_url": callback_url,
            "p_type": "orange_money",
        },
        "redirect": 0,
        "api_key": credentials['api_key'],
        "hash": payment_hash
    }
    url = credentials['api_url']
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers, verify=False)
    if response.status_code == 200:
        payment.payment_url = response.content
        payment.save()
    else:
        raise PaymentException('Error creating payment: {0}'.format(response.content))
    return response.content


def update_payment_status(payment, authenticity, success, failure):
    """
    Check the received status update and update payment status accordingly.
    Note: We can't check status from our site. We have to rely on VitePay sending
    us an update.
    """
    from bluebottle.funding_vitepay.models import VitepayPaymentProvider
    credentials = VitepayPaymentProvider.objects.get().private_settings
    api_secret = credentials['api_secret']
    message = '{order_id};{amount};{currency};{api_secret}'.format(
        order_id=payment.unique_id,
        amount=int(payment.donation.amount.amount * 100),
        currency=payment.donation.amount.currency,
        api_secret=api_secret
    )

    update_hash = hashlib.sha1(message).hexdigest().upper()
    if authenticity != update_hash:
        raise PaymentException('Authenticity incorrect.')
    elif success and failure:
        raise PaymentException('Both failure and success are set. Not sure what to do.')
    elif not success and not failure:
        raise PaymentException('Both failure and success are not set. Not sure what to do.')
    elif failure:
        payment.transitions.fail()
    else:
        payment.transitions.succeed()
    payment.save()
    return payment
