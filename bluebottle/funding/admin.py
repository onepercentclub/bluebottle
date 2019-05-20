from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.models import Funding, Donation
from bluebottle.utils.admin import FSMAdmin
from bluebottle.utils.forms import FSMModelForm


class FundingAdminForm(FSMModelForm):
    class Meta:
        model = Funding
        exclude = ['status', ]


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
    form = FundingAdminForm
    inlines = (DonationInline,)
    base_model = Funding

    readonly_fields = ['amount_raised', ]


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
