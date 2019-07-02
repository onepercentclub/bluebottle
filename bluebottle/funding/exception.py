class PaymentException(Exception):
    """ Wrapper around Payment error messages. """

    def __init__(self, message, error_list=None):
        self.message = message
        self.error_list = error_list

    def __str__(self):
        return str(self.message)

    def __unicode__(self):
        return unicode(self.message)


class PaymentAdminException(Exception):
    pass
