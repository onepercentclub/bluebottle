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
    readonly_fields = ('amount', 'status', )
    extra = 0

    def has_add_permission(self, request):
        return False


class FundingAdmin(ActivityChildAdmin):
    form = FundingAdminForm
    inlines = (DonationInline, )
    base_model = Funding


admin.site.register(Funding, FundingAdmin)
