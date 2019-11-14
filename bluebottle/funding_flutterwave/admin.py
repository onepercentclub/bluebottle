from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from rave_python import Rave
from rave_python.rave_exceptions import SubaccountCreationError

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import Payment, PaymentProvider
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider, \
    FlutterwaveBankAccount


@admin.register(FlutterwavePayment)
class FlutterwavePaymentAdmin(PaymentChildAdmin):
    base_model = Payment


@admin.register(FlutterwavePaymentProvider)
class FlutterwavePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(FlutterwaveBankAccount)
class FlutterwaveBankAccountAdmin(BankAccountChildAdmin):
    model = FlutterwaveBankAccount

    fields = BankAccountChildAdmin.fields + (
        'account_holder_name', 'bank_country_code',
        'bank_code', 'account_number', 'account')

    def get_urls(self):
        urls = super(FlutterwaveBankAccountAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<account_id>.+)/generate-account/$',
                self.admin_site.admin_view(self.generate_account),
                name='funding_flutterwave_flutterwavebankaccount_generate',
            ),
        ]
        return custom_urls + urls

    def generate_account(self, request, account_id):
        provider = FlutterwavePaymentProvider.objects.get()
        rave = Rave(
            provider.public_settings['pub_key'],
            provider.private_settings['sec_key'],
            usingEnv=False,
            production=settings.LIVE_PAYMENTS_ENABLED
        )
        account = FlutterwaveBankAccount.objects.get(id=account_id)
        details = {
            "account_bank": account.bank_code,
            "account_number": account.account_number,
        }
        response = rave.SubAccount.allSubaccounts(details)
        if len(response['returnedData']['data']['subaccounts']):
            account.account = response['returnedData']['data']['subaccounts'][0]['account_id']
            account.reviewed = True
            account.save()
            payout_url = reverse('admin:funding_flutterwave_flutterwavebankaccount_change', args=(account_id,))
            return HttpResponseRedirect(payout_url)

        details = {
            "account_bank": account.bank_code,
            "account_number": account.account_number,
            "business_name": account.account_holder_name,
            "business_email": account.connect_account.owner.email,
            "country": account.bank_country_code,
            "business_contact": account.connect_account.owner.full_name,
            "business_contact_mobile": "09087930450",
            "business_mobile": "09087930450",
            "split_type": "flat",
            "split_value": "0",
            "meta": [{"metaname": "PayoutAccount", "metavalue": account_id}]
        }
        try:
            response = rave.SubAccount.createSubaccount(details)
            account.account = response['data']['subaccount_id']
            account.verified = True
            account.save()
        except SubaccountCreationError as e:
            message = 'Error creating Flutterwave sub account: {}'.format(e.err["errMsg"])
            self.message_user(request, message, level='ERROR')
        payout_url = reverse('admin:funding_flutterwave_flutterwavebankaccount_change', args=(account_id,))
        return HttpResponseRedirect(payout_url)

    generate_account.short_description = _('Generate account at Flutterwave')
    list_filter = ['bank_code', 'reviewed']
    search_fields = ['account_holder_name', 'account_number']
    list_display = ['created', 'account_holder_name', 'account_number', 'bank_code', 'reviewed']
