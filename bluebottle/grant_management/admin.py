from __future__ import division

import logging
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template import loader
from django.urls import re_path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated
from stripe import StripeError

from bluebottle.activities.admin import (
    ActivityChildAdmin,
    ContributorChildAdmin,
)
from bluebottle.fsm.admin import (
    StateMachineAdmin,
    StateMachineAdminMixin,
    StateMachineFilter,
)
from bluebottle.grant_management.models import (
    GrantApplication,
    GrantDeposit,
    GrantDonor,
    GrantFund,
    GrantPayment,
    GrantPayout,
    GrantProvider,
    LedgerItem,
)
from bluebottle.geo.models import Location
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.segments.models import SegmentType
from bluebottle.updates.admin import UpdateInline
from bluebottle.utils.admin import (
    export_as_csv_action,
)

logger = logging.getLogger(__name__)


@admin.register(GrantDonor)
class GrantDonorAdmin(ContributorChildAdmin):
    raw_id_fields = ContributorChildAdmin.raw_id_fields + ('payout',)


class GrantInline(StateMachineAdminMixin, admin.StackedInline):
    model = GrantDonor
    extra = 0
    readonly_fields = ["created", "state_name", "contributor_date", "activity"]
    raw_id_fields = ['fund']
    fields = ['amount', 'fund'] + readonly_fields

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and isinstance(obj, GrantApplication) and obj.target:
            formset.form.base_fields["amount"].initial = obj.target
        return formset


class GrantTabularInline(StateMachineAdminMixin, TabularInlinePaginated):
    model = GrantDonor
    extra = 0
    readonly_fields = ["activity_display", "state_name", "contributor_date", "amount"]
    fields = readonly_fields

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def activity_display(self, obj):
        if obj.activity:
            url = reverse(
                "admin:funding_grantapplication_change", args=(obj.activity.id,)
            )
            return format_html('<a href="{}">{}</a>', url, obj.activity)
        return "-"

    activity_display.short_description = _("Grant application")

    can_delete = False


class LedgerItemInline(TabularInlinePaginated):
    model = LedgerItem
    readonly_fields = ["created", "status", "amount", "type"]

    fields = readonly_fields
    extra = 0

    def has_delete_permission(self, *args, **kwargs):
        return False


class GrantDonorInline(admin.StackedInline):
    model = GrantDonor
    readonly_fields = ["created", "status", "amount"]

    fields = readonly_fields
    extra = 0


class GrantDepositInline(StateMachineAdminMixin, admin.StackedInline):
    model = GrantDeposit
    readonly_fields = ["created", "state_name"]
    fields = ['amount', 'reference', ] + readonly_fields
    extra = 0

    def has_delete_permission(self, *args, **kwargs):
        return False

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.currency:
            formset.form.base_fields["amount"].initial = (None, obj.currency)
        return formset


@admin.register(GrantFund)
class GrantFundAdmin(admin.ModelAdmin):
    inlines = [GrantTabularInline, LedgerItemInline, GrantDepositInline]
    model = GrantFund
    raw_id_fields = ['organization']
    search_fields = ['name', 'description']
    list_display = [
        'name', 'balance', 'total_debit', 'total_credit', 'organization', 'approved_grants'
    ]
    readonly_fields = ['balance', 'total_debit', 'total_credit']

    def has_delete_permission(self, request, obj=None):
        return obj and obj.total_debit == 0

    def approved_grants(self, obj):
        return obj.grants.count()

    approved_grants.short_description = _('Approved grants')


@admin.register(GrantPayout)
class GrantPayoutAdmin(StateMachineAdmin):
    readonly_fields = [
        "total_amount",
        "currency",
        "date_approved",
        "date_started",
        "date_completed",
        "activity",
        "partner_organization",
        "account_details",
        "bank_details",
        "provider"
    ]

    list_filter = [
        StateMachineFilter,
    ]

    list_display = ['activity', 'total_amount', 'state_name', 'created']

    def partner_organization(self, obj):
        if obj.activity and obj.activity.organization:
            url = reverse('admin:organizations_organization_change', args=(obj.activity.organization.id,))
            return format_html('<a href="{}">{}</a>', url, obj.activity.organization)
        return None

    def bank_details(self, obj):
        try:
            template = loader.get_template(
                'admin/funding_stripe/stripebankaccount/detail_fields.html'
            )
            return template.render({'info': obj.activity.bank_account.account})
        except StripeError as e:
            return "Error retrieving details: {}".format(e)
    bank_details.short_description = _('Bank details')

    def account_details(self, obj):
        account = obj.activity.bank_account.connect_account.account
        individual = account.get('individual', None)
        business = account.get('business_profile', None)
        if individual:
            template = loader.get_template(
                'admin/funding_stripe/stripepayoutaccount/detail_fields.html'
            )
            return template.render({'info': individual})
        if business:
            template = loader.get_template(
                'admin/funding_stripe/stripepayoutaccount/business_fields.html'
            )
            return template.render({'info': business})
        return _("Bank account details not available")
    account_details.short_description = _('KYC details')

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                _("Manage"),
                {
                    "fields": [
                        "total_amount",
                        "activity",
                        "partner_organization",
                        "account_details",
                        "bank_details",
                        "date_approved",
                        "date_started",
                        "date_completed",
                        "status",
                        "states",
                        "provider"
                    ],
                },
            ),
        ]

        if request.user.is_superuser:
            fieldsets.append(
                (
                    _("Super admin"),
                    {
                        "fields": [
                            "force_status",
                        ],
                    },
                )
            )

        return fieldsets


class GrantPayoutInline(StateMachineAdminMixin, admin.TabularInline):

    model = GrantPayout
    readonly_fields = [
        "payout_link",
        "total_amount",
        "provider",
        "currency",
        "date_approved",
        "date_started",
        "date_completed",
    ]
    fields = readonly_fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def payout_link(self, obj):
        url = reverse("admin:grant_management_grantpayout_change", args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


class GrantPaymentInline(admin.TabularInline):
    model = GrantPayment
    readonly_fields = ["created", "grant_provider"]
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class GrantFundInline(admin.TabularInline):
    model = GrantFund
    readonly_fields = ["name", "total_debit", "total_credit", "balance"]
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GrantProvider)
class GrantProviderAdmin(admin.ModelAdmin):
    list_display = ["name"]
    inlines = [GrantPaymentInline, GrantFundInline]
    change_form_template = "admin/grant_management/grantprovider/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r"^(?P<pk>.+)/create-payments/$",
                self.admin_site.admin_view(self.create_payment),
                name="funding_grantprovider_create_payments",
            ),
        ]
        return custom_urls + urls

    def create_payment(self, request, pk):
        provider = self.get_object(request, pk)
        if provider is None:
            return HttpResponseRedirect(
                reverse("admin:grant_management_grantprovider_changelist")
            )

        grants = GrantDonor.objects.filter(
            fund__grant_provider=provider,
            payout__status="approved",
            payout__payment=None,
        )

        created_count = 0
        for grant in grants:
            payout = grant.payout
            payment, created = GrantPayment.objects.get_or_create(
                grant_provider=provider, status="new"
            )
            if created:
                created_count += 1
            payout.payment = payment
            payout.save()

        self.message_user(
            request, f"Successfully created {created_count} grant payments."
        )

        return HttpResponseRedirect(
            reverse("admin:grant_management_grantprovider_change", args=[pk])
        )


@admin.register(GrantPayment)
class GrantPaymentAdmin(StateMachineAdminMixin, admin.ModelAdmin):
    list_display = ["created", "grant_provider"]
    list_filter = [StateMachineFilter, "grant_provider"]
    inlines = [GrantPayoutInline]
    change_form_template = "admin/funding/grantpayment/change_form.html"
    readonly_fields = [
        "created",
        "total",
        "grant_provider",
        "state_name",
        "checkout_id",
        "get_payment_link",
    ]
    fields = readonly_fields

    def get_payment_link(self, obj):
        if obj.payment_link:
            title = _("payment link")
            return format_html(
                f'<a href="{obj.payment_link}" target="_blank">{title}</a>'
            )
        return "-"

    get_payment_link.short_description = _("Payment Link")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r"^(?P<pk>.+)/generate-payment-link/$",
                self.admin_site.admin_view(self.generate_payment_link_view),
                name="funding_grantpayment_generate_payment_link",
            ),
            re_path(
                r"^(?P<pk>.+)/check-status/$",
                self.admin_site.admin_view(self.check_status_view),
                name="funding_grantpayment_check_status",
            ),
        ]
        return custom_urls + urls

    def generate_payment_link_view(self, request, pk):
        payment = self.get_object(request, pk)
        if payment is None:
            return HttpResponseRedirect(
                reverse("admin:funding_grantpayment_changelist")
            )

        try:
            payment.generate_payment_link()
            self.message_user(request, _("Successfully generated payment link"))
        except Exception as e:
            self.message_user(request, str(e), level=messages.ERROR)

        return HttpResponseRedirect(
            reverse("admin:funding_grantpayment_change", args=[pk])
        )

    def check_status_view(self, request, pk):
        payment = self.get_object(request, pk)
        if payment is None:
            return HttpResponseRedirect(
                reverse("admin:funding_grantpayment_changelist")
            )

        try:
            payment.check_status()
            self.message_user(request, _("Successfully checked payment status"))
        except Exception as e:
            self.message_user(request, str(e), level=messages.ERROR)

        return HttpResponseRedirect(
            reverse("admin:funding_grantpayment_change", args=[pk])
        )


@admin.register(GrantApplication)
class GrantApplicationAdmin(ActivityChildAdmin):
    inlines = [GrantInline, GrantPayoutInline, UpdateInline, MessageAdminInline]

    base_model = GrantApplication
    list_filter = [
        StateMachineFilter,
    ]
    list_display = [
        "title",
        "target",
        "status",
    ]

    def get_list_display(self, request):
        return self.list_display

    readonly_fields = ActivityChildAdmin.readonly_fields + [
        "started",
    ]

    search_fields = ["title", "description"]
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['bank_account', 'impact_location']

    status_fields = (
        "initiative",
        "owner",
        "slug",
        "highlight",
        "created",
        "updated",
        'started',
        "has_deleted_data",
        "status",
        "states",
    )

    detail_fields = [
        "title",
        "target",
        "description",
        "image",
        "video_url",
        "organization",
        "theme",
        "impact_location",
        "bank_account",
    ]

    def get_fieldsets(self, request, obj=None):
        settings = InitiativePlatformSettings.objects.get()
        fieldsets = [
            (_("Management"), {"fields": self.get_status_fields(request, obj)}),
            (_("Information"), {"fields": self.get_detail_fields(request, obj)}),
        ]
        if Location.objects.count():
            if settings.enable_office_restrictions:
                if "office_restriction" not in self.office_fields:
                    self.office_fields += ("office_restriction",)
                fieldsets.append((_("Office"), {"fields": self.office_fields}))

        if request.user.is_superuser:
            fieldsets.append((_("Super admin"), {"fields": ("force_status",)}))

        if SegmentType.objects.count():
            fieldsets.append(
                (
                    _("Segments"),
                    {
                        "fields": [
                            segment_type.field_name
                            for segment_type in SegmentType.objects.all()
                        ]
                    },
                )
            )
        return fieldsets

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('target', 'Target'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('bank_account', 'Bank Account'),
        ('office_location', 'Office Location'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]
