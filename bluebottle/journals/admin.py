from django.contrib import admin
from .models import DonationJournal, OrganizationPayoutJournal, ProjectPayoutJournal
from .forms import DonationJournalForm, OrganizationPayoutJournalForm, ProjectPayoutJournalForm


class JournalAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.user_reference = request.user
        obj.save()


class DonationJournalAdmin(JournalAdmin):
    model = DonationJournal
    form = DonationJournalForm
    raw_id_fields = ('donation',)
    list_display = ('amount', 'donation', 'user_reference')


class OrganizationPayoutJournalAdmin(JournalAdmin):
    model = OrganizationPayoutJournal
    form = OrganizationPayoutJournalForm
    raw_id_fields = ("payout",)
    list_display = ('amount', 'payout', 'user_reference')


class ProjectPayoutJournalAdmin(JournalAdmin):
    model = ProjectPayoutJournal
    form = ProjectPayoutJournalForm
    raw_id_fields = ("payout",)
    list_display = ('amount', 'payout', 'user_reference')


admin.site.register(DonationJournal, DonationJournalAdmin)
admin.site.register(OrganizationPayoutJournal, OrganizationPayoutJournalAdmin)
admin.site.register(ProjectPayoutJournal, ProjectPayoutJournalAdmin)
