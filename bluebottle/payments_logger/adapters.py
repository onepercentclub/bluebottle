import logging
from .models import PaymentLogEntry, PaymentLogLevels

class PaymentLogAdapter:

    def __init__(self, logger):
        self.logger = logging.getLogger(logger)

    def log(self, payment, level, message):

        if level == PaymentLogLevels.error:
            self.logger.error("{0} - {1}".format(payment, message))
            # Send mail to developer

        log_entry = PaymentLogEntry(payment=payment, level=level, message=message)
        log_entry.save()