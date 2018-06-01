from polymorphic.admin import PolymorphicChildModelAdmin

from django.contrib import admin

from bluebottle.payments.models import Payment
from bluebottle.payments_interswitch.models import InterswitchPaymentStatusUpdate
from .models import InterswitchPayment


class InterswitchPaymentStatusInlineAdmin(admin.StackedInline):
    model = InterswitchPaymentStatusUpdate
    extra = 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class InterswitchPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = InterswitchPayment
    inlines = [InterswitchPaymentStatusInlineAdmin]
    raw_id_fields = ('order_payment', )


admin.site.register(InterswitchPayment, InterswitchPaymentAdmin)
