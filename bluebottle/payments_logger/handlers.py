import logging
from .models import PaymentLogEntry


class PaymentLogHandler(logging.Handler, object):
    def emit(self, record):
        payment = record.args.get('payment')
        message = "{0} - {1}".format(payment, record.msg)

        log_entry = PaymentLogEntry(payment=payment, level=record.levelname, message=message)
        log_entry.save()

        return log_entry.pk
