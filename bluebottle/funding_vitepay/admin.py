from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin
from bluebottle.funding_vitepay.models import StripePayment


@admin.register(StripePayment)
class VitepayPaymentAdmin(PaymentChildAdmin):
    base_model = StripePayment
