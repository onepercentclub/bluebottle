import sys

from io import StringIO

import requests
from django.core.management import call_command
from django.conf import settings

models = [

    # Initiative
    {
        'title': 'States - Initiative',
        'model': 'bluebottle.initiatives.models.Initiative',
        'page_id': '742588583'
    },
    {
        'title': 'States - Activity Organizer',
        'model': 'bluebottle.activities.models.Organizer',
        'page_id': '742588590'
    },

    # Funding
    {
        'title': 'States - Funding - Donor',
        'model': 'bluebottle.funding.models.Donor',
        'page_id': '739999825'
    },
    {
        'title': 'States - Funding - Money Contribution',
        'model': 'bluebottle.funding.models.MoneyContribution',
        'page_id': '1179975917'
    },
    {
        'title': 'States - Funding - Fundraising Campaign',
        'model': 'bluebottle.funding.models.Funding',
        'page_id': '742359054'
    },

    {
        'title': 'States - Funding - Plain Payout Account',
        'model': 'bluebottle.funding.models.PlainPayoutAccount',
        'page_id': '742654079'
    },
    {
        'title': 'States - Funding - Stripe Payout Account',
        'model': 'bluebottle.funding_stripe.models.StripePayoutAccount',
        'page_id': '742654093'
    },
    {
        'title': 'States - Funding - Payout',
        'model': 'bluebottle.funding.models.Payout',
        'page_id': '742326440'
    },
    {
        'title': 'States - Funding - Stripe Source Payment',
        'model': 'bluebottle.funding_stripe.models.StripeSourcePayment',
        'page_id': '742326474'
    },
    {
        'title': 'States - Funding - Stripe Intent Payment',
        'model': 'bluebottle.funding_stripe.models.StripePayment',
        'page_id': '742326447'
    },
    {
        'title': 'States - Funding - Pledge Payment',
        'model': 'bluebottle.funding_pledge.models.PledgePayment',
        'page_id': '750977260'
    },
    {
        'title': 'States - Funding - Flutterwave Payment',
        'model': 'bluebottle.funding_flutterwave.models.FlutterwavePayment',
        'page_id': '750977317'
    },
    {
        'title': 'States - Funding - Lipisha Payment',
        'model': 'bluebottle.funding_lipisha.models.LipishaPayment',
        'page_id': '750944494'
    },
    {
        'title': 'States - Funding - Vitepay Payment',
        'model': 'bluebottle.funding_vitepay.models.VitepayPayment',
        'page_id': '750911678'
    },

    {
        'title': 'States - Funding - Stripe External Account',
        'model': 'bluebottle.funding_stripe.models.ExternalAccount',
        'page_id': '1051688967'
    },
    {
        'title': 'States - Funding - Pledge Bank Account',
        'model': 'bluebottle.funding_pledge.models.PledgeBankAccount',
        'page_id': '1050116137'
    },
    {
        'title': 'States - Funding - Flutterwave Bank Account',
        'model': 'bluebottle.funding_flutterwave.models.FlutterwaveBankAccount',
        'page_id': '1050116130'
    },
    {
        'title': 'States - Funding - Lipisha Bank Account',
        'model': 'bluebottle.funding_lipisha.models.LipishaBankAccount',
        'page_id': '1050279943'
    },
    {
        'title': 'States - Funding - Vitepay Bank Account',
        'model': 'bluebottle.funding_vitepay.models.VitepayBankAccount',
        'page_id': '1050148912'
    },

    # Time-based Activities
    {
        'title': 'States - Time based - Activity on a date',
        'model': 'bluebottle.time_based.models.DateActivity',
        'page_id': '1120731198'
    },
    {
        'title': 'States - Time based - Participant on a date',
        'model': 'bluebottle.time_based.models.DateParticipant',
        'page_id': '1180041279'
    },
    {
        'title': 'States - Time based - Activity over a period',
        'model': 'bluebottle.time_based.models.PeriodActivity',
        'page_id': '1120731205'
    },
    {
        'title': 'States - Time based - Participant over a period',
        'model': 'bluebottle.time_based.models.PeriodParticipant',
        'page_id': '1179975839'
    },
    {
        'title': 'States - Time based - Time contribution',
        'model': 'bluebottle.time_based.models.TimeContribution',
        'page_id': '1180008621'
    },

]

api = settings.CONFLUENCE['api']


def run(*args):

    for model in models:
        url = "{}/wiki/rest/api/content/{}".format(api['domain'], model['page_id'])
        response = requests.get(url, auth=(api['user'], api['key']))
        data = response.json()
        version = data['version']['number'] + 1
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        call_command('print_transitions', model['model'])
        sys.stdout = old_stdout
        html = result.getvalue()
        html = html.encode('ascii', 'ignore')

        data = {
            "id": model['page_id'],
            "type": "page",
            "status": "current",
            "title": model['title'],
            "version": {
                "number": version
            },
            "body": {
                "storage": {
                    "value": html,
                    "representation": "storage"
                }
            }
        }
        url += '?expand=body.storage'
        response = requests.put(url, json=data, auth=(api['user'], api['key']))
        if response.status_code == 200:
            print("[OK] {}".format(model['title']))
        else:
            print("[ERROR] {}".format(model['title']))
