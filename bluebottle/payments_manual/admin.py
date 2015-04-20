from django.contrib import admin

from bluebottle.payments.models import Payment
from .models import ManualPayment


class ManualPaymentAdmin(admin.ModelAdmin):
    base_model = Payment
    model = ManualPayment

admin.site.register(ManualPayment, ManualPaymentAdmin)
