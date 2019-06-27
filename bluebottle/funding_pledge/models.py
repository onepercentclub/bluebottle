from bluebottle.funding.models import Payment


class PledgePayment(Payment):

    def save(self, *args, **kwargs):
        if self.status == self.Status.new:
            self.succeed()

        super(PledgePayment, self).save(*args, **kwargs)

    def request_refund(self):
        pass
