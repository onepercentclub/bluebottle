from babel.numbers import get_currency_name, get_currency_symbol

from bluebottle.funding.models import PaymentProvider


def get_currency_settings():
    result = []
    for provider in PaymentProvider.objects.all():
        for cur in provider.paymentcurrency_set.all():
            result.append({
                'provider': provider.name,
                'code': cur.code,
                'name': get_currency_name(cur.code),
                'symbol': get_currency_symbol(cur.code).replace('US$', '$'),
                'defaultAmounts': [
                    cur.default1,
                    cur.default2,
                    cur.default3,
                    cur.default4,
                ],
                'minAmount': cur.min_amount,
                'maxAmount': cur.max_amount
            })
    return result
