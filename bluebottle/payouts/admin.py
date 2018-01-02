import logging
import re
import decimal

from django import forms
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext as _

from bluebottle.bb_payouts.models import (ProjectPayoutLog,
                                          OrganizationPayoutLog)
from bluebottle.clients import properties
from bluebottle.payouts.models import ProjectPayout, OrganizationPayout
from bluebottle.utils.admin import export_as_csv_action
from bluebottle.utils.utils import StatusDefinition

from .admin_utils import link_to

logger = logging.getLogger(__name__)


class PayoutLogBase(admin.TabularInline):
    extra = 0
    max_num = 0
    can_delete = False
    fields = ['created', 'old_status', 'new_status']
    readonly_fields = fields


class PayoutLogInline(PayoutLogBase):
    model = ProjectPayoutLog


class OrganizationPayoutLogInline(PayoutLogBase):
    model = OrganizationPayoutLog


class ProjectPayoutForm(forms.ModelForm):
    payout_rule = forms.ChoiceField(
        choices=ProjectPayout.PayoutRules.choices)

    class Meta:
        model = ProjectPayout
        exclude = ()


class BasePayoutAdmin(admin.ModelAdmin):
    actions = ['change_status_to_in_progress',
               'change_status_to_settled',
               'change_status_to_retry',
               'recalculate_amounts']

    def change_status_to_retry(self, request, queryset):
        for payout in queryset.all():
            payout.retry()
            payout.save()

    def change_status_to_in_progress(self, request, queryset):
        for payout in queryset.all():
            payout.in_progress()
            payout.save()

    def change_status_to_settled(self, request, queryset):
        for payout in queryset.all():
            payout.settled()
            payout.save()

    def recalculate_amounts(self, request, queryset):
        # Only recalculate for 'new' payouts
        filter_args = {'status': StatusDefinition.NEW}
        qs_new = queryset.all().filter(**filter_args)

        for payout in qs_new:
            payout.calculate_amounts()
            payout.save()

        new_payouts = qs_new.count()
        skipped_payouts = queryset.exclude(**filter_args).count()
        message = ("Fees for {0} new payouts were recalculated. "
                   "{1} progressing or closed payouts have"
                   "been skipped.").format(new_payouts, skipped_payouts)

        self.message_user(request, message)

    recalculate_amounts.short_description = _("Recalculate amounts for new "
                                              "payouts.")


class BaseProjectPayoutAdmin(BasePayoutAdmin):
    model = ProjectPayout
    form = ProjectPayoutForm
    inlines = (PayoutLogInline,)

    search_fields = [
        'invoice_reference', 'receiver_account_iban', 'receiver_account_number',
        'project__title', 'project__organization__name'
    ]

    date_hierarchy = 'updated'
    can_delete = False

    list_filter = ['status', 'payout_rule']

    readonly_fields = ['admin_project', 'admin_organization', 'created', 'status',
                       'updated']

    fieldsets = (
        (None, {
            'fields': (
                'admin_project', 'admin_organization',
                'status', 'invoice_reference', 'protected'
            )
        }),
        (_('Dates'), {
            'fields': (
                'created', 'updated', 'submitted', 'completed',
            )
        }),
        (_('Payout amounts'), {
            'fields': ('amount_raised', 'organization_fee', 'amount_payable',
                       'payout_rule')
        }),
        (_('Payment details'), {
            'fields': (
                'receiver_account_name', 'receiver_account_country',
                'receiver_account_number', 'receiver_account_iban',
                'receiver_account_details', 'description_line1',
                'description_line2', 'description_line3', 'description_line4'
            )
        })
    )

    def is_pending(self, obj):
        """ Whether or not there is no amount pending. """
        if obj.get_amount_pending() == decimal.Decimal('0.00'):
            return False

        return True

    is_pending.boolean = True
    is_pending.short_description = _('pending')

    def created_date(self, obj):
        return obj.created.strftime("%d-%m-%Y")

    created_date.admin_order_field = 'created'
    created_date.short_description = 'created'

    def submitted_date(self, obj):
        if obj.submitted:
            return obj.submitted.strftime("%d-%m-%Y")
        return ""

    submitted_date.admin_order_field = 'submitted'
    submitted_date.short_description = 'Submitted'

    def completed_date(self, obj):
        if obj.completed:
            return obj.completed.strftime("%d-%m-%Y")
        return ""

    completed_date.admin_order_field = 'completed'
    completed_date.short_description = 'Completed'

    # Link to project
    admin_project = link_to(
        lambda obj: obj.project,
        'admin:projects_project_change',
        view_args=lambda obj: (obj.project.id,),
        short_description=_('project'),
        truncate=25
    )

    # Link to organization
    admin_organization = link_to(
        lambda obj: obj.project.organization,
        'admin:organizations_organization_change',
        view_args=lambda obj: (obj.project.organization.id,),
        short_description=_('organization')
    )

    def admin_has_iban(self, obj):
        if obj.receiver_account_iban and obj.receiver_account_details:
            return True

        return False

    admin_has_iban.short_description = _('IBAN')
    admin_has_iban.boolean = True

    def payout(self, obj):
        return "View"

    def has_add_permission(self, request):
        return False

    def rule(self, obj):
        return dict(ProjectPayout.PayoutRules.choices)[obj.payout_rule]


admin.site.register(ProjectPayout, BaseProjectPayoutAdmin)


class BaseOrganizationPayoutAdmin(BasePayoutAdmin):
    inlines = [OrganizationPayoutLogInline]

    can_delete = False

    search_fields = ['invoice_reference']

    date_hierarchy = 'start_date'

    list_filter = ['status', ]

    list_display = [
        'invoice_reference', 'start_date', 'end_date', 'status',
        'organization_fee_incl', 'psp_fee_incl',
        'other_costs_incl', 'payable_amount_incl'
    ]

    readonly_fields = [
        'invoice_reference', 'organization_fee_excl', 'organization_fee_vat',
        'organization_fee_incl', 'psp_fee_excl', 'psp_fee_vat', 'psp_fee_incl',
        'payable_amount_excl', 'payable_amount_vat', 'payable_amount_incl',
        'other_costs_vat', 'status'
    ]

    fieldsets = (
        (None, {
            'fields': (
                'status', 'invoice_reference'
            )
        }),
        (_('Dates'), {
            'fields': (
                'start_date', 'end_date', 'planned', 'completed'
            )
        }),
        (_('Organization fee'), {
            'fields': (
                'organization_fee_excl', 'organization_fee_vat',
                'organization_fee_incl'
            )
        }),
        (_('PSP fee'), {
            'fields': (
                'psp_fee_excl', 'psp_fee_vat', 'psp_fee_incl'
            )
        }),
        (_('Other costs'), {
            'fields': (
                'other_costs_excl', 'other_costs_vat', 'other_costs_incl'
            )
        }),
        (_('Amount payable'), {
            'fields': (
                'payable_amount_excl', 'payable_amount_vat',
                'payable_amount_incl'
            )
        })
    )


admin.site.register(OrganizationPayout, BaseOrganizationPayoutAdmin)


class PayoutListFilter(admin.SimpleListFilter):
    title = _('Payout rule')
    parameter_name = 'payout_rule'

    def lookups(self, request, model_admin):
        rules = getattr(properties, 'PROJECT_PAYOUT_FEES', {})

        def _value(label):
            value = re.search(r'\d+', label)
            try:
                return int(value.group(0))
            except Exception:
                return None

        def _label(v, k):
            return "{0:.3g}% ({1})".format(v * 100, k)

        return tuple(sorted(((k, _label(v, k)) for k, v in rules.iteritems()),
                            key=lambda x: _value(x[1])))

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        else:
            return queryset.filter(payout_rule=self.value())


class LegacyPayoutListFilter(admin.SimpleListFilter):
    title = _('Legacy payout rule')
    parameter_name = 'legacy_payout_rule'

    def lookups(self, request, model_admin):
        return (
            ('old', _('Old')),
            ('zero', _('0%')),
            ('five', _('5%')),
            ('seven', _('7%')),
            ('twelve', _('12%')),
            ('hundred', _('100%')),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        else:
            return queryset.filter(payout_rule=self.value())


class OrganizationPayoutAdmin(BaseOrganizationPayoutAdmin):
    actions = ('export_sepa',)

    def export_sepa(self, request, queryset):
        """
        Dowload a sepa file with selected ProjectPayments
        """
        objs = queryset.all()
        if not request.user.is_staff:
            raise PermissionDenied
        response = HttpResponse(mimetype='text/xml')
        date = timezone.datetime.strftime(timezone.now(), '%Y%m%d%H%I%S')
        response['Content-Disposition'] = 'attachment; ' \
                                          'filename=payments_sepa%s.xml' % date
        response.write(OrganizationPayout.create_sepa_xml(objs))
        return response

    export_sepa.short_description = "Export SEPA file."


try:
    admin.site.unregister(OrganizationPayout)
except NotRegistered:
    pass
admin.site.register(OrganizationPayout, OrganizationPayoutAdmin)


class ProjectPayoutAdmin(BaseProjectPayoutAdmin):
    list_display = ['payout', 'status', 'admin_project', 'amount_pending',
                    'amount_raised', 'amount_pledged', 'amount_payable',
                    # 'percent',
                    'admin_has_iban', 'created_date',
                    'submitted_date', 'completed_date']

    export_fields = [
        ('project', 'project'),
        ('status', 'status'),
        ('payout_rule', 'payout rule'),
        ('amount_raised', 'amount raised'),
        ('organization_fee', 'organization fee'),
        ('amount_payable', 'amount payable'),
        ('created', 'created'),
        ('submitted', 'submitted')
    ]

    actions = ('change_status_to_new', 'change_status_to_progress',
               'change_status_to_settled', 'export_sepa', 'recalculate_amounts',
               export_as_csv_action(fields=export_fields))

    def get_list_filter(self, request):
        # If site has a legacy payout rule then display the legacy filter
        if ProjectPayout.objects.filter(
                payout_rule__in=['old', 'five', 'seven', 'twelve',
                                 'hundred']).count():
            return ['status', PayoutListFilter, LegacyPayoutListFilter]
        else:
            return ['status', PayoutListFilter]

    def export_sepa(self, request, queryset):
        """
        Dowload a sepa file with selected ProjectPayments
        """
        objs = queryset.all()
        if not request.user.is_staff:
            raise PermissionDenied
        response = HttpResponse()
        date = timezone.datetime.strftime(timezone.now(), '%Y%m%d%H%I%S')
        response['Content-Disposition'] = 'attachment; ' \
                                          'filename=payments_sepa%s.xml' % date
        response.write(ProjectPayout.create_sepa_xml(objs))
        return response

    export_sepa.short_description = "Export SEPA file."


try:
    admin.site.unregister(ProjectPayout)
except NotRegistered:
    pass
admin.site.register(ProjectPayout, ProjectPayoutAdmin)
