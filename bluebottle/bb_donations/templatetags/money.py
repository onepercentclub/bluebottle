from bluebottle.clients.utils import get_currencies
from django import template

register = template.Library()


@register.filter()
def format_money(value):
    symbol = [currency['symbol'] for currency in get_currencies()
              if currency['code'] == str(value.currency)][0]

    return '{} {}'.format(symbol.encode('utf-8'), value.amount)
