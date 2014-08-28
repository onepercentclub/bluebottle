from django.contrib import admin
from django.core.urlresolvers import reverse
from bluebottle.payments_logger.models import PaymentLogEntry


class PaymentLogEntryAdmin(admin.ModelAdmin):
    # List view.
    list_display = ('payment', 'timestamp', 'level', 'message')
    list_filter = ('level', )
    search_fields = ('message', 'level', 'payment')

    # def payment(self, obj):
    #     payment = obj.payment
    #     url = reverse('admin:%s_%s_change' % (payment._meta.app_label, payment._meta.module_name), args=[payment.id])
    #     return "<a href='%s'>%s</a>" % (str(url), payment)
    #
    # payment.allow_tags = True
    #
    # # Don't allow the detail view to be accessed.
    # def has_change_permission(self, request, obj=None):
    #     if not obj:
    #         return True
    #     return False

admin.site.register(PaymentLogEntry, PaymentLogEntryAdmin)
