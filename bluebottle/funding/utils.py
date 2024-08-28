from babel.numbers import get_currency_name, get_currency_symbol
from bluebottle.utils.exchange_rates import convert
from django.db.models import Sum
from djmoney.money import Money

from bluebottle.funding.models import PaymentProvider


def get_currency_settings():
    result = {}
    for provider in PaymentProvider.objects.all():
        for cur in provider.paymentcurrency_set.all():
            if cur.code not in result:
                result[cur.code] = {
                    'provider': provider.name,
                    'providerName': provider.title,
                    'code': cur.code,
                    'name': get_currency_name(cur.code),
                    'symbol': get_currency_symbol(cur.code).replace('US$', '$').replace('NGN', '₦'),
                    'defaultAmounts': [
                        cur.default1,
                        cur.default2,
                        cur.default3,
                        cur.default4,
                    ],
                    'minAmount': cur.min_amount,
                    'maxAmount': cur.max_amount
                }
    return list(result.values())


def calculate_total(queryset, target='EUR'):
    totals = queryset.values(
        'donor__payout_amount_currency'
    ).annotate(
        total=Sum('donor__payout_amount')
    ).order_by('-created')
    amounts = [Money(tot['total'], tot['donor__payout_amount_currency']) for tot in totals]
    amounts = [convert(amount, target) for amount in amounts]
    return sum(amounts) or Money(0, target)
