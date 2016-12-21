from djmoney_rates.utils import convert_money


def convert(money, currency):
    """ Convert money object `money` to `currency`."""
    return convert_money(money.amount, money.currency, currency)
