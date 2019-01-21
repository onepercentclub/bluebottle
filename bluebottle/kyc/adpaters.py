import stripe


class StripeAdapter(object):

    def __init__(self, secret_key):
        stripe.api_key = secret_key

    def create_account(self, user, country='NL'):
        account = stripe.Account.create(
            country=country,
            type='custom'
        )
        return account
