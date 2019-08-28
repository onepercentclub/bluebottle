from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from rave_python import Rave
from rave_python.rave_exceptions import SubaccountCreationError

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, PayoutAccountChildAdmin
from bluebottle.funding.models import PayoutAccount
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider, \
    FlutterwavePayoutAccount


@admin.register(FlutterwavePayment)
class FlutterwavePaymentAdmin(PaymentChildAdmin):
    base_model = FlutterwavePayment


@admin.register(FlutterwavePaymentProvider)
class FlutterwavePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = FlutterwavePaymentProvider


@admin.register(FlutterwavePayoutAccount)
class FlutterwavePayoutAccountAdmin(PayoutAccountChildAdmin):
    base_model = PayoutAccount
    model = FlutterwavePayoutAccount

    fields = PayoutAccountChildAdmin.fields + (
        'account_holder_name', 'bank_country_code',
        'bank_code', 'account_number', 'account')

    def get_urls(self):
        urls = super(FlutterwavePayoutAccountAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<account_id>.+)/generate-account/$',
                self.admin_site.admin_view(self.generate_account),
                name='flutterwave-payout-generate-account',
            ),
        ]
        return custom_urls + urls

    def generate_account(self, request, account_id):
        account = FlutterwavePayoutAccount.objects.get(id=account_id)
        details = {
            "account_bank": account.bank_code,
            "account_number": account.account_number,
            "business_name": account.account_holder_name,
            "business_email": account.owner.email,
            "country": account.bank_country_code,
            "business_contact": account.owner.full_name,
            "business_contact_mobile": "",
            "business_mobile": "",
            "split_type": "flat",
            "split_value": 0,
            "meta": [{"metaname": "PayoutAccount", "metavalue": account_id}]
        }
        provider = FlutterwavePaymentProvider.objects.get()
        rave = Rave(
            provider.public_settings['pub_key'],
            provider.private_settings['sec_key'],
            usingEnv=False,
            production=settings.LIVE_PAYMENTS_ENABLED
        )
        try:
            response = rave.SubAccount.createSubaccount(details)
            account.account = response['data']['subaccount_id']
            account.transitions.verify()
            account.save()
        except SubaccountCreationError as e:
            message = 'Error creating Flutterwave sub account: {}'.format(e.err["errMsg"])
            self.message_user(request, message, level='ERROR')
        payout_url = reverse('admin:funding_flutterwave_flutterwavepayoutaccount_change', args=(account_id,))
        return HttpResponseRedirect(payout_url)

    generate_account.short_description = _('Generate account at Flutterwave')
