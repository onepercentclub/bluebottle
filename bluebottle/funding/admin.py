from django.contrib import admin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.models import Funding, Donation
from bluebottle.utils.admin import ReviewAdmin
from bluebottle.utils.forms import FSMModelForm


class FundingAdminForm(FSMModelForm):
    class Meta:
        model = Funding
        exclude = ['status', ]


class DonationInline(admin.TabularInline):
    model = Donation

    raw_id_fields = ('user',)
    readonly_fields = ('status',)
    extra = 0


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
class DonationAdmin(ReviewAdmin):
    raw_id_fields = ['activity', 'user']
    model = Donation
    form = DonationAdminForm
    list_display = ['user', 'status', 'amount']
