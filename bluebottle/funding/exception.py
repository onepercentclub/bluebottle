from builtins import str

from future.utils import python_2_unicode_compatible


@python_2_unicode_compatible
class PaymentException(Exception):
    """ Wrapper around Payment error messages. """

    def __init__(self, message, error_list=None):
        self.message = message
        self.error_list = error_list

    def __str__(self):
        return str(self.message)


class PaymentAdminException(Exception):
    pass
