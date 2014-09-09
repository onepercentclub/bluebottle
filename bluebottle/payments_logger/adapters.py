import logging
from .models import PaymentLogEntry

class PaymentLogAdapter:

    def __init__(self, logger='payments.payment'):
        # get the logger defined in the base.py file (so far payments.payment)
        self.logger = logging.getLogger(logger)

    def log(self, payment, level, message):

        log_context = "{0} - {1}".format(payment, message)

        getattr(self.logger, level)(log_context)

        log_entry = PaymentLogEntry(payment=payment, level=level, message=message)
        log_entry.save()
