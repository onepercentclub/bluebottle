from bluebottle.funding.models import Payment


class PledgePayment(Payment):

    def save(self, *args, **kwargs):
        if self.status == self.Status.new:
            self.success()

        super(PledgePayment, self).save(*args, **kwargs)

    @Payment.status.transition(
        source=['success'],
        target='refund_requested'
    )
    def request_refund(self):
        self.refund()
