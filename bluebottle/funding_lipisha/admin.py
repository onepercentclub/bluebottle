from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, PayoutAccountChildAdmin
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaPaymentProvider, LipishaPayoutAccount


@admin.register(LipishaPayment)
class LipishaPaymentAdmin(PaymentChildAdmin):
    base_model = LipishaPayment


@admin.register(LipishaPaymentProvider)
class LipishaPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = LipishaPaymentProvider


@admin.register(LipishaPayoutAccount)
class LipishaPayoutAccountAdmin(PayoutAccountChildAdmin):
    model = LipishaPayoutAccount
    fields = PayoutAccountChildAdmin.fields + ('account_number',)
