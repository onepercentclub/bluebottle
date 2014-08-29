# from django.contrib import admin
# from polymorphic.admin import PolymorphicParentModelAdmin
# from bluebottle.payments.models import Payment, OrderPayment, OrderPaymentAction, OrderPaymentStatuses
# from bluebottle.payments_docdata.admin import DocdataPaymentChildAdmin
# from bluebottle.payments_docdata.models import DocdataPayment
#
#
# class PaymentParentAdmin(PolymorphicParentModelAdmin):
#     """ The parent model admin """
#     base_model = Payment
#     list_display = ('order_payment', 'created', 'updated')
#     ordering = ('-created', )
#     child_models = (
#         (DocdataPayment, DocdataPaymentChildAdmin),
#     )
#
# admin.site.register(Payment, PaymentParentAdmin)
# admin.site.register(DocdataPayment, DocdataPaymentChildAdmin)
#
#
# class OrderPaymentActionInlineAdmin(admin.ModelAdmin):
#     model = OrderPaymentAction
#
#
# class OrderPaymentStatusesInlineAdmin(admin.ModelAdmin):
#     model = OrderPaymentStatuses
#
#
# class OrderPaymentAdmin(admin.ModelAdmin):
#
#     model = OrderPayment
#
#     list_display = ('user', 'order', 'status', 'amount', 'created', 'updated', 'closed', 'payment_method')
#     list_filter = ('status', )
#     search_fields = ('user', 'order', 'status', 'payment_method')
#
# admin.site.register(OrderPayment, OrderPaymentAdmin)