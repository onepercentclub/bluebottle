from django.conf import settings
from djmoney.contrib.exchange.models import convert_money


def convert(money, currency):
    """ Convert money object `money` to `currency`."""
    if hasattr(currency, 'code'):
        currency = currency.code

    if money.currency.code == currency:
        return money

    if money.currency.code != settings.BASE_CURRENCY and currency != settings.BASE_CURRENCY:
        money = convert_money(money, settings.BASE_CURRENCY)

    return convert_money(money, currency)
