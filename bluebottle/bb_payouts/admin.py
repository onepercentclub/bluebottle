import logging
from bluebottle.utils.model_dispatcher import get_project_payout_model, get_organization_payout_model, get_model_mapping
from bluebottle.utils.utils import StatusDefinition

logger = logging.getLogger(__name__)

import decimal

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.text import Truncator

from .models import ProjectPayoutLog, OrganizationPayoutLog

from .admin_filters import HasIBANPayoutFilter
from .admin_utils import link_to
from django import forms

PROJECT_PAYOUT_MODEL = get_project_payout_model()
ORGANIZATION_PAYOUT_MODEL = get_organization_payout_model()
MODEL_MAP = get_model_mapping()


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
    payout_rule = forms.ChoiceField(choices=PROJECT_PAYOUT_MODEL.PayoutRules.choices)

    class Meta:
        model = PROJECT_PAYOUT_MODEL


class ProjectPayoutAdmin(admin.ModelAdmin):
    model = PROJECT_PAYOUT_MODEL
    form = ProjectPayoutForm
    inlines = (PayoutLogInline, )

    search_fields = [
        'invoice_reference', 'receiver_account_iban', 'receiver_account_number',
        'project__title', 'project__organization__name'
    ]

    date_hierarchy = 'updated'
    can_delete = False

    list_filter = ['status', 'payout_rule']

    actions = ['change_status_to_new', 'change_status_to_progress', 'change_status_to_settled',
               'recalculate_amounts']

    def change_status_to_new(self, request, queryset):
        for payout in queryset.all():
            payout.status = StatusDefinition.NEW
            payout.save()

    def change_status_to_progress(self, request, queryset):
        for payout in queryset.all():
            payout.status = StatusDefinition.IN_PROGRESS
            payout.save()

    def change_status_to_settled(self, request, queryset):
        for payout in queryset.all():
            payout.status = StatusDefinition.SETTLED
            payout.save()

    list_display = ['payout', 'status', 'admin_project', 'amount_payable', 'rule',
                    'admin_has_iban', 'created_date', 'submitted_date', 'completed_date']

    list_display_links = ['payout']

    readonly_fields = ['admin_project', 'admin_organization', 'created', 'updated']

    fieldsets = (
        (None, {
            'fields': (
                'admin_project', 'admin_organization',
                'status', 'invoice_reference'
            )
        }),
        (_('Dates'), {
            'fields': (
                'created', 'updated', 'submitted', 'completed',
            )
        }),
        (_('Payout amounts'), {
            'fields': ('amount_raised', 'organization_fee', 'amount_payable', 'payout_rule')
        }),
        (_('Payment details'), {
            'fields': (
                'receiver_account_name', 'receiver_account_country', 'receiver_account_number',
                'receiver_account_iban', 'receiver_account_bic',
                'description_line1', 'description_line2', 'description_line3', 'description_line4'
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
        'admin:{0}_{1}_change'.format(MODEL_MAP['project']['app'], MODEL_MAP['project']['class'].lower()),
        view_args=lambda obj: (obj.project.id, ),
        short_description=_('project'),
        truncate=50
    )

    # Link to organization
    admin_organization = link_to(
        lambda obj: obj.project.organization,
        'admin:organizations_organization_change',
        view_args=lambda obj: (obj.project.organization.id, ),
        short_description=_('organization')
    )

    def admin_has_iban(self, obj):
        if obj.receiver_account_iban and obj.receiver_account_bic:
            return True

        return False
    admin_has_iban.short_description = _('IBAN')
    admin_has_iban.boolean = True

    def payout(self, obj):
        return "Select"

    def has_add_permission(self, request):
        return False

    def recalculate_amounts(self, request, queryset):
        # Only recalculate for 'new' payouts
        filter_args = {'status': StatusDefinition.NEW}
        qs_new = queryset.all().filter(**filter_args)

        for payout in qs_new:
            payout.calculate_amounts()

        message = (
            "Fees for %(new_payouts)d new payouts were recalculated. "
            "%(skipped_payouts)d progressing or closed payouts have been skipped."
        ) % {
            'new_payouts': qs_new.count(),
            'skipped_payouts': queryset.exclude(**filter_args).count()
        }

        self.message_user(request, message)

    recalculate_amounts.short_description = _("Recalculate amounts for new payouts.")

    def rule(self, obj):
        return dict(PROJECT_PAYOUT_MODEL.PayoutRules.choices)[obj.payout_rule]


admin.site.register(PROJECT_PAYOUT_MODEL, ProjectPayoutAdmin)


class OrganizationPayoutAdmin(admin.ModelAdmin):
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
        'invoice_reference', 'organization_fee_excl', 'organization_fee_vat', 'organization_fee_incl',
        'psp_fee_excl', 'psp_fee_vat', 'psp_fee_incl',
        'payable_amount_excl', 'payable_amount_vat', 'payable_amount_incl',
        'other_costs_vat'
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
                'organization_fee_excl', 'organization_fee_vat', 'organization_fee_incl'
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
                'payable_amount_excl', 'payable_amount_vat', 'payable_amount_incl'
            )
        })
    )

    actions = ('recalculate_amounts', )

    def recalculate_amounts(self, request, queryset):
        # Only recalculate for 'new' payouts
        filter_args = {'status': StatusDefinition.NEW}
        qs_new = queryset.all().filter(**filter_args)

        for payout in qs_new:
            payout.calculate_amounts()

        message = (
            "Amounts for %(new_payouts)d new payouts were recalculated. "
            "%(skipped_payouts)d progressing or closed payouts have been skipped."
        ) % {
            'new_payouts': qs_new.count(),
            'skipped_payouts': queryset.exclude(**filter_args).count()
        }

        self.message_user(request, message)

    recalculate_amounts.short_description = _("Recalculate amounts for new payouts.")


admin.site.register(ORGANIZATION_PAYOUT_MODEL, OrganizationPayoutAdmin)


