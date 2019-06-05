from django.db import models, connection
from bluebottle.funding_stripe import stripe

from bluebottle.funding.models import Payment


class StripePayment(Payment):
    intent_id = models.CharField(max_length=30)
    client_secret = models.CharField(max_length=30)

    def save(self, *args, **kwargs):
        if not self.pk:
            intent = stripe.PaymentIntent.create(
                amount=self.donation.amount.amount,
                currency=self.donation.amount.currency,
                transfer_data={'destination': self.donation.activity.account.account_id},
                metadata=self.metadata
            )
            self.intent_id = intent.id
            self.client_secret = intent.client_secret

        super(StripePayment, self).save(*args, **kwargs)

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
