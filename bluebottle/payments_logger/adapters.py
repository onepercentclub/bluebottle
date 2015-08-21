import logging


class PaymentLogAdapter:
    def __init__(self, logger='payments.payment'):
        # get the logger defined in the base.py file (so far payments.payment)
        self.logger = logging.getLogger(logger)

    def log(self, payment, level, message):
        args = {
            'payment': payment
        }

        getattr(self.logger, level.lower())(message, args)
