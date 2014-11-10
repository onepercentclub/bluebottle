from bluebottle.payments.exception import PaymentException


class DocdataPaymentException(PaymentException):
    """ Wrapper around Docdata error messages. """

    def __init__(self, message, error_list=None):
        self.message = message
        self.error_list = error_list


class DocdataPaymentStatusException(PaymentException):
    """ Thrown when unknown payment statuses are received. """

    def __init__(self, message, report_type, data=None):
        self.message = message
        self.report_type = report_type
        self.data = data

    def __str__(self):
        return '%s, report type %s, data %s' % (self.message,
                                                self.report_type,
                                                self.data)

    def __unicode__(self):
        return str(self)
