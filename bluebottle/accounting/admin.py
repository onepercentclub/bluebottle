from decimal import Decimal
from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib import admin
from django.db.models.aggregates import Sum, Count
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from djchoices import DjangoChoices, ChoiceItem

from bluebottle.payments.models import OrderPayment
from bluebottle.utils.utils import StatusDefinition

from .models import BankTransactionCategory
from .signals import match_transaction_with_payout
from ..csvimport.admin import IncrementalCSVImportMixin

from .models import BankTransaction, RemoteDocdataPayment, RemoteDocdataPayout
from .forms import (
    BankTransactionImportForm, DocdataPaymentImportForm,
    update_remote_docdata_status,
    bulk_update_remote_docdata_spanning_multiple_weeks
)
from .admin_extra import (
    DocdataPaymentMatchedListFilter, OrderPaymentMatchedListFilter,
    OrderPaymentIntegrityListFilter, IntegrityStatusListFilter
)
from .admin_views import (
    UnknownTransactionView, CreateProjectPayoutJournalView,
    CreateOrganizationPayoutJournalView, CreateManualDonationView,
    RetryPayoutView
)


admin.site.register(BankTransactionCategory)


class BankTransactionAdmin(IncrementalCSVImportMixin, admin.ModelAdmin):
    date_hierarchy = 'book_date'

    actions = ('find_matches', )

    search_fields = [
        'counter_account', 'counter_name',
        'description1', 'description2', 'description3', 'description4',
        'description5', 'description6',
        'amount'
    ]

    list_display = [
        'book_date', 'counter_name', 'counter_account', 'credit_debit', 'amount', 'status',
        'status_remarks', 'show_actions', 'category',
    ]

    list_filter = [
        'credit_debit', 'book_date', 'category', IntegrityStatusListFilter,
    ]

    raw_id_fields = ('payout', 'remote_payout', 'remote_payment')

    readonly_fields = ('payout_link', 'remote_payout_link', 'remote_payment_link',
                       'counter_name', 'counter_account', 'sender_account',
                       'description1', 'description2', 'description3',
                       'description4', 'description5', 'description6',
                       'credit_debit', 'currency', 'book_code', 'book_date', 'interest_date',
                       'amount', 'filler', 'end_to_end_id', 'id_recipient', 'mandate_id',)

    fieldsets = (
        (None, {
            'fields': ('status', 'status_remarks', 'category')
        }),
        ('Data', {
            'fields': readonly_fields
        }),
    )

    import_form = BankTransactionImportForm
    ordering = ('-book_date',)

    def queryset(self, request):
        return super(BankTransactionAdmin, self).queryset(request).select_related('payout', 'remote_payout')

    def payout_link(self, obj):
        object = obj.payout
        url = reverse('admin:%s_%s_change' % (object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='%s'>%s (%s)</a>" % (str(url), object, object.amount)
    payout_link.allow_tags = True

    def remote_payout_link(self, obj):
        object = obj.remote_payout
        url = reverse('admin:%s_%s_change' % (object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='%s'>%s</a> Payout amount %s" % (str(url), object, object.payout_amount)
    remote_payout_link.allow_tags = True

    def remote_payment_link(self, obj):
        object = obj.remote_payment
        url = reverse('admin:%s_%s_change' % (object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='%s'>%s</a> Amount collected %s" % (str(url), object, object.amount_collected)
    remote_payout_link.allow_tags = True

    def show_actions(self, obj):
        """
        Collect the possible actions depending on ``obj.status``.
        """
        is_credit = obj.credit_debit == BankTransaction.CreditDebit.credit
        actions = {
            # 'amount_mismatch': '<a href="#">%s</a>' % _('todo'),
            BankTransaction.IntegrityStatus.UnknownTransaction: (
                '<a href="%s">%s</a>' % (
                    reverse('admin:banktransaction-unknown', kwargs={'pk': obj.pk}),
                    _('manual entry')
                ),
                '<a href="%s">%s</a>' % (
                    reverse('admin:banktransaction-add-manualdonation', kwargs={'pk': obj.pk}),
                    _('create donation')
                ) if is_credit else None,
                '<a href="%s">%s</a>' % (
                    reverse('admin:banktransaction-retry-payout', kwargs={'pk': obj.pk}),
                    _('retry payout')
                ) if is_credit else None
            )
        }
        actions = [a for a in (actions.get(obj.status) or []) if a is not None]
        return " &bull; ".join(actions)
    show_actions.allow_tags = True
    show_actions.short_description = _('actions')

    def find_matches(self, request, queryset):
        #
        for transaction in queryset.all():
            match_transaction_with_payout(transaction)
    find_matches.short_description = _("Try to match with payouts.")

    def get_urls(self):
        """
        Extra urls to save manual entries.
        """
        urls = super(BankTransactionAdmin, self).get_urls()
        action_urls = patterns(
            '',
            url(
                r'^(?P<pk>\d+)/unknown_transaction/$',
                self.admin_site.admin_view(UnknownTransactionView.as_view()),
                name='banktransaction-unknown'
            ),
            url(
                r'^(?P<pk>\d+)/unknown_transaction/projectpayout/$',
                self.admin_site.admin_view(CreateProjectPayoutJournalView.as_view()),
                name='banktransaction-add-projectpayoutjournal'
            ),
            url(
                r'^(?P<pk>\d+)/unknown_transaction/organization_payout/$',
                self.admin_site.admin_view(CreateOrganizationPayoutJournalView.as_view()),
                name='banktransaction-add-organizationpayoutjournal'
            ),
            url(
                r'^(?P<pk>\d+)/unknown_transaction/manual_donation/$',
                self.admin_site.admin_view(CreateManualDonationView.as_view()),
                name='banktransaction-add-manualdonation',
            ),
            url(
                r'^(?P<pk>\d+)/unknown_transaction/retry_payout/$',
                self.admin_site.admin_view(RetryPayoutView.as_view()),
                name='banktransaction-retry-payout'
            )
        )
        return action_urls + urls


class DocdataPaymentInline(admin.TabularInline):
    model = RemoteDocdataPayment
    readonly_fields = ['triple_deal_reference', 'merchant_reference', 'payment_type', 'amount_collected',
                       'currency_amount_collected', 'tpci', 'docdata_fee']
    fields = readonly_fields


class DocdataPayoutAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'

    search_fields = ['payout_reference']

    list_display = ['payout_reference', 'week', 'start_date', 'end_date', 'payout_date', 'payout_amount',
                    'payments_total', 'local_payments_total']

    readonly_fields = ['payout_reference', 'payout_date', 'payout_amount',
                       'start_date', 'end_date', 'collected_amount',
                       'payments_count', 'payments_total', 'fee_total', 'costs_total', 'vat_costs',
                       'local_payments_total', 'local_payments_count']

    fieldsets = (
        (None, {
            'fields': ('payout_reference', 'payout_date', 'payout_amount',
                       'start_date', 'end_date', 'collected_amount')
        }),
        ('Calculated from remote payments', {
            'fields': ('payments_count', 'payments_total', 'fee_total', 'costs_total', 'vat_costs')
        }),
        ('Calculated from local order-payments', {
            'fields': ('local_payments_count', 'local_payments_total', )
        })
    )

    inlines = [DocdataPaymentInline,]

    def week(self, obj):
        if obj.start_date:
            return 'Week {0}'.format(obj.start_date.isocalendar()[1])
        return '?'

    def local_payments_total(self, obj):
        order_payment_ids = obj.remotedocdatapayment_set.values_list('local_payment__order_payment__id')
        order_payments = OrderPayment.objects.filter(id__in=order_payment_ids)
        order_payments = order_payments.filter(status=StatusDefinition.SETTLED)
        total = order_payments.aggregate(total=Sum('amount'))['total']
        return format(total)

        # return obj.remotedocdatapayment_set.filter(local_payment__order_payment__status=StatusDefinition.SETTLED).aggregate(total=Sum('local_payment__order_payment__amount'))['total']

    def local_payments_count(self, obj):
        payment_ids = obj.remotedocdatapayment_set.values_list('local_payment_id')
        return len(payment_ids)

    def payments_count(self, obj):
        count = obj.remotedocdatapayment_set.count()
        url = '/admin/accounting/remotedocdatapayment/'
        return "<a href='{0}?remote_payout__id__exact={1}'>{2} payments</a>".format(url, obj.id, count)
    payments_count.allow_tags = True

    def payments_total(self, obj):
        total = obj.remotedocdatapayment_set.aggregate(total=Sum('amount_collected'))
        return total['total']

    def fee_total(self, obj):
        return obj.remotedocdatapayment_set.aggregate(total=Sum('docdata_fee'))['total']

    def costs_total(self, obj):
        return obj.remotedocdatapayment_set.aggregate(total=Sum('tpci'))['total']

    def vat_costs(self, obj):
        costs = self.costs_total(obj) + self.fee_total(obj)
        return round(Decimal(settings.VAT_RATE) * costs * 100) / 100


class DocdataPaymentAdmin(IncrementalCSVImportMixin, admin.ModelAdmin):
    actions = ('find_matches',)

    list_display = [
        'triple_deal_reference', 'payout_date', 'merchant_reference', 'payment_type',
        'payment_link', 'matched', 'status', 'status_remarks',
    ]

    list_filter = ['payment_type', DocdataPaymentMatchedListFilter, IntegrityStatusListFilter]

    readonly_fields = ['payout_link', 'payment_link', 'merchant_reference', 'triple_deal_reference',
                       'payment_type', 'amount_collected', 'currency_amount_collected', 'tpci',
                       'docdata_fee']

    fieldsets = (
        (None, {
            'fields': ('status', 'status_remarks',)
        }),
        ('Data', {
            'fields': readonly_fields
        }),
    )

    search_fields = ['merchant_reference', 'triple_deal_reference', 'remote_payout__payout_reference']

    import_form = DocdataPaymentImportForm

    def queryset(self, request):
        return super(DocdataPaymentAdmin, self).queryset(request).select_related(
            'local_payment', 'remote_payout'
        ).annotate(
            rdp_amount_collected_sum=Sum('local_payment__remotedocdatapayment__amount_collected')
        )

    def payout_date(self, obj):
        if obj.remote_payout:
            return obj.remote_payout.payout_date
        return None
    payout_date.admin_order_field = 'remote_payout__payout_date'

    def payment_link(self, obj):
        payment = obj.local_payment
        if payment:
            url = reverse('admin:%s_%s_change' % (
                payment._meta.app_label, payment._meta.module_name), args=[payment.id])
            return "<a href='%s'>%s</a>" % (str(url), payment)
        return '-'
    payment_link.allow_tags = True

    def matched(self, obj):
        return bool(obj.local_payment)
    matched.boolean = True

    def payout_link(self, obj):
        object = obj.remote_payout
        url = reverse('admin:%s_%s_change' % (object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='%s'>%s</a>" % (str(url), object)
    payout_link.allow_tags = True

    def find_matches(self, request, queryset):
        for rdp in queryset.all():
            update_remote_docdata_status(rdp)
            rdp.save()
        bulk_update_remote_docdata_spanning_multiple_weeks(queryset.all())
    find_matches.short_description = _("Try to match with backoffice.")


class OrderPaymentIntegrityStatuses(DjangoChoices):
    missing_docdata = ChoiceItem('missing_docdata', _('Invalid: Missing docdata payment'))
    missing_remote_docdata = ChoiceItem('missing_remote_docdata', _('Invalid: Missing remote docdata payment'))
    amount_mismatch = ChoiceItem('amount_mismatch', _('Invalid: Amount mismatch ({0} != {1})'))
    valid = ChoiceItem('valid', _('Valid'))


class OrderPaymentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    raw_id_fields = ('user', )
    readonly_fields = ('order_link', 'payment_link', 'remote_payment_link',
                       'authorization_action', 'amount', 'integration_data',
                       'payment_method', 'transaction_fee', 'status', 'created', 'closed')
    fields = ('user',) + readonly_fields
    list_display = ('created', 'user', 'status', 'amount', 'payment_method',
                    'transaction_fee', 'triple_deal_reference', 'matched',
                    'integrity_status', 'show_actions')
    list_filter = ('status', 'created', 'payment_method',
                   OrderPaymentMatchedListFilter, OrderPaymentIntegrityListFilter)
    ordering = ('-created',)

    def queryset(self, request):
        return super(OrderPaymentAdmin, self).queryset(request).select_related('payment').annotate(
            rdp_amount_collected=Sum('payment__remotedocdatapayment__amount_collected'),
            n_journals=Count('journals')
        )

    def triple_deal_reference(self, obj):
        return ', '.join(obj.payment.remotedocdatapayment_set.values_list('triple_deal_reference', flat=True))

    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>Order: {1}</a>".format(str(url), object.id)
    order_link.allow_tags = True

    def payment_link(self, obj):
        object = obj.payment
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>{1}: {2}</a>".format(str(url), object.polymorphic_ctype, object.id)
    payment_link.allow_tags = True

    def remote_payment_link(self, obj):
        if obj.n_journals:
            url = 'admin:journals_orderpaymentjournal_change'
            return u', '.join('<a href="%s">%s</a>' % (reverse(url, args=[journal.pk]), _('journal'))
                              for journal in obj.journals.all())
        if self.matched(obj):
            object = obj.payment.remotedocdatapayment_set.all()[0]
            url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
            return "<a href='{0}'>Remote Docdata Payment: {1}</a>".format(str(url), object.id)
    remote_payment_link.allow_tags = True

    def matched(self, obj):
        if obj.payment and (obj.payment.remotedocdatapayment_set.exists() or obj.n_journals):
            return True
        return False
    matched.boolean = True

    def _get_integrity_status(self, obj):
        if not hasattr(obj, '_integrity_status'):
            if not obj.payment:
                obj._integrity_status = OrderPaymentIntegrityStatuses.missing_docdata
            elif not obj.payment.remotedocdatapayment_set.exists() and not obj.n_journals:
                obj._integrity_status = OrderPaymentIntegrityStatuses.missing_remote_docdata
            # The line below is done via annotate.
            # amount_collected = obj.payment.remotedocdatapayment_set.aggregate(
            #     Sum('amount_collected'))['amount_collected__sum']
            elif obj.amount == obj.rdp_amount_collected or obj.n_journals:
                obj._integrity_status = OrderPaymentIntegrityStatuses.valid
            else:
                obj._integrity_status = OrderPaymentIntegrityStatuses.amount_mismatch
        return obj._integrity_status

    def integrity_status(self, obj):
        integrity = self._get_integrity_status(obj)
        return OrderPaymentIntegrityStatuses.labels[integrity].format(obj.amount, obj.rdp_amount_collected)

    def show_actions(self, obj):
        actions = []  # empty list by default
        integrity = self._get_integrity_status(obj)
        if integrity == OrderPaymentIntegrityStatuses.missing_remote_docdata:
            actions = [
                u'<a href="%s" title="%s">%s</a>' % (
                    reverse('admin:accounting_remotedocdatapayment_import'),
                    _('Needs to be settled by importing the payments and matching them.'),
                    _('Keep')
                ),
                u'<a href="%s?%s">%s</a>' % (
                    reverse('admin:journals_orderpaymentjournal_add'),
                    urlencode({
                        'amount': obj.amount,
                        'order_payment': obj.pk,
                        'description': 'remote docdata payment not found'
                    }),
                    _('Manual entry'),
                )
            ]
        return ' &bull; '.join(actions)
    show_actions.allow_tags = True


admin.site.unregister(OrderPayment)
admin.site.register(OrderPayment, OrderPaymentAdmin)

admin.site.register(BankTransaction, BankTransactionAdmin)
admin.site.register(RemoteDocdataPayout, DocdataPayoutAdmin)
admin.site.register(RemoteDocdataPayment, DocdataPaymentAdmin)
