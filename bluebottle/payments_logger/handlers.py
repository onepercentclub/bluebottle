import logging
from .models import PaymentLogEntry


class PaymentLogHandler(logging.Handler, object):
    """
    Log handler for storing payment events as PaymentLogEntry entries in the db
    """
    def emit(self, record):
        # TODO: we should use the formatting features of the logging library
        #       the format the message rather than doing it explicitly here.
        payment = record.args.get('payment')
        message = "{0} - {1}".format(payment, record.msg)

        log_entry = PaymentLogEntry(payment=payment, level=record.levelname, message=message)
        log_entry.save()

        return log_entry.pk
