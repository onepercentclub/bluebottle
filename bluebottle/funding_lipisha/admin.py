from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaPaymentProvider


@admin.register(LipishaPayment)
class LipishaPaymentAdmin(PaymentChildAdmin):
    base_model = LipishaPayment


@admin.register(LipishaPaymentProvider)
class LipishaPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = LipishaPaymentProvider
