from django.contrib import admin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.models import Funding, Donation

from bluebottle.utils.forms import FSMModelForm


class FundingAdminForm(FSMModelForm):
    class Meta:
        model = Funding
        fields = '__all__'


class DonationInline(admin.TabularInline):
    model = Donation

    raw_id_fields = ('user', )
    readonlyfields = ('time_spent', 'status', )


class FundingAdmin(ActivityChildAdmin):
    form = FundingAdminForm
    inlines = (DonationInline, )

    base_model = Funding


admin.site.register(Funding, FundingAdmin)
