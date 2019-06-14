from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.models import Funding, Donation
from bluebottle.utils.admin import FSMAdmin
from bluebottle.utils.forms import FSMModelForm


class DonationInline(admin.TabularInline):
    model = Donation

    raw_id_fields = ('user',)
    readonly_fields = ('donation', 'user', 'amount', 'status',)
    extra = 0

    def donation(self, obj):
        url = reverse('admin:funding_donation_change', args=(obj.id,))
        return format_html('<a href="{}">{} {}</a>',
                           url,
                           obj.created.date(),
                           obj.created.strftime('%H:%M'))


class FundingAdmin(ActivityChildAdmin):
    inlines = (DonationInline,)
    base_model = Funding

    raw_id_fields = ActivityChildAdmin.raw_id_fields

    readonly_fields = ActivityChildAdmin.readonly_fields + ['amount_raised']

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner', 'status', 'status_transition', 'created', 'updated'
        )}),
        (_('Details'), {'fields': (
            'deadline', 'duration',
            'target', 'amount_raised',
            'accepted_currencies',
        )}),
    )


admin.site.register(Funding, FundingAdmin)


class DonationAdminForm(FSMModelForm):
    class Meta:
        model = Donation
        exclude = ['status', ]


@admin.register(Donation)
class DonationAdmin(FSMAdmin):
    raw_id_fields = ['activity', 'user']
    model = Donation
    form = DonationAdminForm
    list_display = ['user', 'status', 'amount']
