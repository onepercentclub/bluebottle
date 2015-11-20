import logging


class PaymentLogHandler(logging.Handler):
    """
    Log handler for storing payment events as PaymentLogEntry entries in the db
    """

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        # NOTE: need to import this here otherwise it causes a circular reference
        #       i.e. settings imports loggers imports models imports settings...
        from bluebottle.payments_logger.models import PaymentLogEntry

        # TODO: we should use the formatting features of the logging library
        #       the format the message rather than doing it explicitly here.
        payment = record.args.get('payment')
        message = "{0} - {1}".format(payment, record.msg)

        log_entry = PaymentLogEntry(payment=payment, level=record.levelname,
                                    message=message)
        log_entry.save()

        return log_entry.pk
