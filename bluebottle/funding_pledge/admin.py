from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin
from bluebottle.funding_pledge.models import PledgePayment


@admin.register(PledgePayment)
class PledgePaymentAdmin(PaymentChildAdmin):
    base_model = PledgePayment
