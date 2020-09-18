from djmoney.contrib.exchange.models import convert_money


def convert(money, currency):
    """ Convert money object `money` to `currency`."""
    return convert_money(money, currency)
