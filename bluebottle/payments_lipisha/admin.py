from polymorphic.admin import PolymorphicChildModelAdmin

from django.contrib import admin
from bluebottle.payments.models import Payment
from bluebottle.payments_lipisha.models import LipishaProject

from .models import LipishaPayment


class LipishaPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = LipishaPayment
    search_fields = ['transaction_mobile', 'transaction_reference']
    raw_id_fields = ('order_payment', )


admin.site.register(LipishaPayment, LipishaPaymentAdmin)


class LipishaProjectAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', )


admin.site.register(LipishaProject, LipishaProjectAdmin)
