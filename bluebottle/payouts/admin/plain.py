from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.admin.utils import PayoutAccountProjectLinkMixin
from bluebottle.payouts.models import PayoutAccount, PlainPayoutAccount, PayoutDocument
from bluebottle.projects.forms import UploadWidget


class PayoutDocumentForm(forms.ModelForm):
    class Meta:
        model = PayoutDocument
        widgets = {
            'file': UploadWidget()
        }
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(PayoutDocumentForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False


@admin.register(PayoutDocument)
class PayoutDocumentAdmin(admin.ModelAdmin):
    model = PayoutDocument
    form = PayoutDocumentForm

    raw_id_fields = ('author',)
    readonly_fields = ('download_url', 'created', 'updated', 'ip_address')
    fields = readonly_fields + ('file', 'author')

    def download_url(self, obj):
        url = obj.document_url

        if url is not None:
            return format_html(
                u"<a href='{}'>{}</a>",
                str(url), _('Download')
            )
        return '(None)'


@admin.register(PlainPayoutAccount)
class PlainPayoutAccountAdmin(PayoutAccountProjectLinkMixin, PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = PlainPayoutAccount
    raw_id_fields = ('user', 'document')
    readonly_fields = ('project_links', 'reviewed')

    fields = (
        'user',
        'project_links',
        'reviewed',
        'document',
        'account_holder_name',
        'account_holder_address',
        'account_holder_postal_code',
        'account_holder_city',
        'account_holder_country',
        'account_number',
        'account_details',
        'account_bank_country'

    )

    def get_urls(self):
        urls = super(PlainPayoutAccountAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<account_id>.+)/reviewed/$',
                self.admin_site.admin_view(self.check_status),
                name='plain-payout-account-reviewed',
            ),
        ]
        return custom_urls + urls

    def check_status(self, request, account_id):
        if request.user.has_perm('payouts.change_plainpayoutaccount'):
            account = PlainPayoutAccount.objects.get(id=account_id)
            account.reviewed = True
            account.save()
            payout_url = reverse('admin:payouts_payoutaccount_change', args=(account_id,))
            return HttpResponseRedirect(payout_url)
        else:
            return HttpResponseForbidden('Missing permission: payouts.change_plainpayoutaccount')

    check_status.short_description = _('Set to reviewed')
