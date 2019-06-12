from django.db import models, connection

from bluebottle.funding_stripe import stripe
from bluebottle.funding.models import Payment
from bluebottle.payouts.models import StripePayoutAccount


class StripePayment(Payment):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if not self.pk:
            intent = stripe.PaymentIntent.create(
                amount=int(self.donation.amount.amount * 100),
                currency=self.donation.amount.currency,
                transfer_data={
                    'destination': StripePayoutAccount.objects.all()[0].account_id,
                },
                metadata=self.metadata
            )
            self.intent_id = intent.id
            self.client_secret = intent.client_secret

        super(StripePayment, self).save(*args, **kwargs)

    def update(self):
        intent = stripe.PaymentIntent.retrieve(self.intent_id)
        if len(intent.charges) == 0:
            # No charge. Do we still need to charge?
            self.fail()
            self.save()
        elif intent.charges.data[0].refunded and self.status != Payment.Status.refunded:
            self.refund()
            self.save()
        elif intent.status == 'failed' and self.status != Payment.Status.failed:
            self.fail()
            self.save()
        elif intent.status == 'succeeded' and self.status != Payment.Status.success:
            self.succeed()
            self.save()

    @property
    def metadata(self):
        return {
            "tenant_name": connection.tenant.client_name,
            "tenant_domain": connection.tenant.domain_url,
            "activity_id": self.donation.activity.pk,
            "activity_title": self.donation.activity.title,
        }

    @Payment.status.transition(
        source=['success'],
        target='refunded'
    )
    def request_refund(self):
        intent = stripe.PaymentIntent.retrieve(self.intent_id)

        intent.charges[0].refund(
            reverse_transfer=True,
        )
