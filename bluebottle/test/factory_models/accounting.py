import factory

from datetime import date, timedelta
from decimal import Decimal

from bluebottle.accounting.models import (BankTransaction, BankTransactionCategory,
                                          RemoteDocdataPayout, RemoteDocdataPayment)
from bluebottle.test.factory_models.payouts import ProjectPayoutFactory

from .payments import PaymentFactory


DEFAULT_CURRENCY = 'EUR'
TODAY = date.today()


class RemoteDocdataPayoutFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = RemoteDocdataPayout

    payout_reference = factory.Sequence(lambda n: 'Reference_{0}'.format(n))

    payout_date = TODAY
    start_date = TODAY - timedelta(days=10)
    end_date = TODAY + timedelta(days=10)
    collected_amount = Decimal('10')
    payout_amount = Decimal('10')


class RemoteDocdataPaymentFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = RemoteDocdataPayment

    merchant_reference = 'merchant reference'
    triple_deal_reference = 'triple deal reference'
    payment_type = 1
    amount_collected = Decimal('10')
    currency_amount_collected = DEFAULT_CURRENCY
    docdata_fee = Decimal('0.25')
    currency_docdata_fee = DEFAULT_CURRENCY

    local_payment = factory.SubFactory(PaymentFactory)
    remote_payout = factory.SubFactory(RemoteDocdataPayoutFactory)

    status = 'valid'  # or 'missing' or 'mismatch' as in RemoteDocdataPayment.IntegretyStatus
    # status_remarks, tpcd, currency_tpcd, tpci, currency_tpci


class BankTransactionCategoryFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = BankTransactionCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Category_{0}'.format(n))


class BankTransactionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = BankTransaction

    category = factory.SubFactory(BankTransactionCategoryFactory)
    # only one of these three make sense, so set 2 on None when using this factory
    payout = factory.SubFactory(ProjectPayoutFactory)
    remote_payout = factory.SubFactory(RemoteDocdataPayoutFactory)
    remote_payment = factory.SubFactory(RemoteDocdataPaymentFactory)

    sender_account = 'NL24RABO0133443493'
    currency = DEFAULT_CURRENCY
    interest_date = TODAY + timedelta(days=30)
    credit_debit = 'C'  # or 'D'
    amount = Decimal('100')

    counter_account = 'NL91ABNA0417164300'
    counter_name = 'Counter name'
    book_date = TODAY
    book_code = 'bg'

    status = 'valid'  # or 'unknown', 'mismatch'  # BankTransaction.IntegrityStatus.choices
    # description1 (t/m description6), end_to_end_id, id_recipient, mandate_id, status_remarks, filler
