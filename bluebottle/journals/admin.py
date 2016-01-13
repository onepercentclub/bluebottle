from django.contrib import admin
from django.core.urlresolvers import reverse
from .models import (
    DonationJournal, OrganizationPayoutJournal, ProjectPayoutJournal,
    OrderPaymentJournal
)

from .forms import journalform_factory


class JournalAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.user_reference = request.user
        obj.save()


class DonationJournalAdmin(JournalAdmin):
    model = DonationJournal
    form = journalform_factory(DonationJournal)
    raw_id_fields = ('donation',)
    list_display = ('amount', 'date', 'donation_link', 'project', 'user_reference')

    def donation_link(self, obj):
        donation_url = reverse('admin:donations_donation_change', args=[obj.donation.id])
        return u'<a href="{}">{}</a>'.format(donation_url, obj.donation)

    def project(self, obj):
        project_url = reverse('admin:projects_project_change', args=[obj.donation.project.id])
        return u'<a href="{}">{}</a>'.format(project_url, obj.donation.project)

    donation_link.allow_tags = True
    project.allow_tags = True


class OrganizationPayoutJournalAdmin(JournalAdmin):
    model = OrganizationPayoutJournal
    form = journalform_factory(OrganizationPayoutJournal)
    raw_id_fields = ("payout",)
    list_display = ('amount', 'date', 'payout_link', 'user_reference')

    def payout_link(self, obj):
        payout_url = reverse('admin:payouts_organizationpayout_change', args=[obj.payout.id])
        return u'<a href="{}">{}</a>'.format(payout_url, obj.payout)

    payout_link.allow_tags = True


class ProjectPayoutJournalAdmin(JournalAdmin):
    model = ProjectPayoutJournal
    form = journalform_factory(ProjectPayoutJournal)
    raw_id_fields = ("payout",)
    list_display = ('amount', 'date', 'payout_link', 'project', 'user_reference')

    def payout_link(self, obj):
        payout_url = reverse('admin:payouts_projectpayout_change', args=[obj.payout.id])
        return u'<a href="{}">{}</a>'.format(payout_url, obj.payout)

    def project(self, obj):
        project_url = reverse('admin:projects_project_change', args=[obj.payout.project.id])
        return u'<a href="{}">{}</a>'.format(project_url, obj.payout.project)

    payout_link.allow_tags = True
    project.allow_tags = True


class OrderPaymentJournalAdmin(JournalAdmin):
    form = journalform_factory(OrderPaymentJournal)
    raw_id_fields = ('order_payment',)

    def order_payment_link(self, obj):
        url = reverse('admin:payments_orderpayment_change', args=[obj.order_payment.pk])
        return u'<a href="{}">{}</a>'.format(url, obj.order_payment)


admin.site.register(DonationJournal, DonationJournalAdmin)
admin.site.register(OrganizationPayoutJournal, OrganizationPayoutJournalAdmin)
admin.site.register(ProjectPayoutJournal, ProjectPayoutJournalAdmin)
admin.site.register(OrderPaymentJournal, OrderPaymentJournalAdmin)
