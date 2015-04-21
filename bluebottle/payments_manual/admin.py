from django.contrib import admin

from bluebottle.payments.models import Payment
from .models import ManualPayment


class ManualPaymentAdmin(admin.ModelAdmin):
    base_model = Payment
    model = ManualPayment

    def has_add_permission(self, request):
        """
        The entire order/payment flow has to be strictly followed. You cannot
        manually add manual payments, ever.
        """
        return False

admin.site.register(ManualPayment, ManualPaymentAdmin)
