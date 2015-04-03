from django.db.models import Sum, Count
from django.db.models.query import QuerySet
from django.utils import timezone

from .models import BankTransaction, RemoteDocdataPayment, RemoteDocdataPayout, BankTransactionCategory
from .enum import BANK_ACCOUNTS

from decimal import Decimal


def add_up(first, second):
    """
    Addition of two objects.

    Distinguish addition of dictionaries, list, querysets and numbers.

    return None when both are None
    if one of the two is None, return the other one which is not None

    if both are dictionaries, add them up with the custom mydict.__add__

    if both are convertable to a Decimal, return the addition of the numbers

    in other cases, return 'first' if it is equal to 'second' without caring about the type
    and when they are not equal, return None because we don't know how to handle that
    """
    if not first:
        return second
    elif not second:
        return first
    else:
        if isinstance(first, mydict) and isinstance(second, mydict):
            return first + second
        elif isinstance(first, mylist) and isinstance(second, mylist):
            return first.add(second)
        elif isinstance(first, QuerySet) and isinstance(second, QuerySet):
            return None # first | second
        else:
            try:
                result = Decimal(str(first)) + Decimal(str(second))
                return result
            except:
                if first == second:  # if both are some Class like a DjangoModel
                    return first
                else:
                    # both are NOT None, they are different and are not a dict and not numeric
                    print 'Could not handle addition of {} and {}'.format(type(first), type(second))
                    return None


class mydict(dict):

    def __add__(self, dict2):
        if self == mydict():
            return dict2

        keys = self.keys()
        assert set(keys) == set(dict2.keys())

        new_dict = mydict()
        for key in keys:
            new_dict[key] = add_up(self[key], dict2[key])

        return new_dict


class mylist(list):

    def add(self, list2):
        length = len(self)
        assert length == len(list2)

        return mylist([add_up(self[i], list2[i]) for i in range(length)])


def get_datefiltered_qs(start, stop):
    from bluebottle.donations.models import Donation
    from bluebottle.payments.models import OrderPayment
    from bluebottle.payouts.models import ProjectPayout

    data = mydict()
    data['transactions'] = BankTransaction.objects.filter(book_date__gte=start, book_date__lte=stop)
    data['order_payments'] = OrderPayment.objects.filter(created__gte=start, created__lte=stop)
    data['remote_docdata_payments'] = RemoteDocdataPayment.objects.filter(remote_payout__payout_date__gte=start, remote_payout__payout_date__lte=stop)
    data['remote_docdata_payouts'] = RemoteDocdataPayout.objects.filter(payout_date__gte=start, payout_date__lte=stop)

    exluded_date = timezone.datetime(2014, 7, 8)

    data['project_payouts'] = ProjectPayout.objects.exclude(
        created__gte=exluded_date,
        created__lt=exluded_date + timezone.timedelta(days=1),
        )
    data['donations'] = Donation.objects.filter(created__gte=start, created__lte=stop)
    return data

def get_dashboard_values(start, stop):
    data = get_datefiltered_qs(start, stop)

    # Mismatches
    data['invalid_transactions'] = data['transactions'].exclude(status=BankTransaction.IntegrityStatus.Valid)
    data['invalid_transactions_count'] = data['invalid_transactions'].count()
    data['invalid_transactions_amount'] = data['invalid_transactions'].aggregate(Sum('amount'))['amount__sum'] or 0
    data['invalid_order_payments'] = data['order_payments'].filter(payment=None)
    invalid_payments = data['invalid_order_payments'].aggregate(Sum('amount'), Sum('transaction_fee'))
    data['invalid_order_payments_amount'] = invalid_payments['amount__sum'] or 0
    data['invalid_order_payments_count'] = data['invalid_order_payments'].count()
    data['invalid_order_payments_transaction_fee'] = invalid_payments['transaction_fee__sum'] or 0

    data['donations_failed'] = data['donations'].filter(order__status='failed')
    data['donations_failed_amount'] = data['donations_failed'].aggregate(Sum('amount'))['amount__sum'] or 0
    data['donations_failed_count'] = data['donations_failed'].count()

    # Aggregated totals
    data['transactions_amount'] = data['transactions'].aggregate(Sum('amount'))['amount__sum'] or 0
    data['transactions_count'] = data['transactions'].count()
    data['order_payments_amount'] = data['order_payments'].aggregate(Sum('amount'))['amount__sum'] or 0
    data['order_payments_count'] = data['order_payments'].count()
    data['remote_docdata_payments_amount'] = data['remote_docdata_payments'].aggregate(Sum('amount_collected'))['amount_collected__sum'] or 0
    data['remote_docdata_payments_count'] = data['remote_docdata_payments'].count()
    data['remote_docdata_payouts_amount'] = data['remote_docdata_payouts'].aggregate(Sum('payout_amount'))['payout_amount__sum'] or 0
    data['remote_docdata_payouts_count'] = data['remote_docdata_payouts'].count()
    data['project_payouts_amount'] = data['project_payouts'].aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
    data['project_payouts_count'] = data['project_payouts'].count()
    data['project_payouts_pending'] = data['project_payouts'].exclude(status='settled')
    data['project_payouts_pending_amount'] = data['project_payouts_pending'].aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
    data['project_payouts_settled'] = data['project_payouts'].filter(status='settled')
    data['project_payouts_settled_amount'] = data['project_payouts_settled'].aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
    data['project_payouts_settled_count'] = data['project_payouts_settled'].count()
    data['project_payouts_pending_new'] = data['project_payouts'].filter(status='new')
    data['project_payouts_pending_new_amount'] = data['project_payouts_pending_new'].aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
    data['project_payouts_pending_new_count'] = data['project_payouts_pending_new'].count()
    data['project_payouts_pending_in_progress'] = data['project_payouts'].filter(status='in_progress')
    data['project_payouts_pending_in_progress_amount'] = data['project_payouts_pending_in_progress'].aggregate(Sum('amount_raised'))['amount_raised__sum'] or 0
    data['project_payouts_pending_in_progress_count'] = data['project_payouts_pending_in_progress'].count()
    data['donations_count'] = data['donations'].count()
    data['donations_amount'] = data['donations'].aggregate(Sum('amount'))['amount__sum'] or 0
    data['donations_settled'] = data['donations'].filter(order__status='success')
    data['donations_settled_amount'] = data['donations_settled'].aggregate(Sum('amount'))['amount__sum'] or 0
    data['donations_settled_count'] = data['donations_settled'].count()

    return data

def get_accounting_statistics(start, stop):
    statistics = mydict()
    data = get_datefiltered_qs(start, stop)

    order_payments = data['order_payments'].filter(status__in=['settled', 'charged_back', 'refunded'])
    order_payments_aggregated = order_payments.aggregate(Sum('amount'), Sum('transaction_fee'))

    bank_transactions = data['transactions']

    remote_docdata_payments = data['remote_docdata_payments']
    remote_docdata_payments_aggregated = remote_docdata_payments.aggregate(Sum('amount_collected'), Sum('docdata_fee'), Sum('tpci'))

    remote_docdata_payouts = data['remote_docdata_payouts']
    remote_docdata_payouts_aggregated = remote_docdata_payouts.aggregate(Sum('payout_amount'))

    project_payouts = data['project_payouts'].filter(completed__gte=start, completed__lte=stop)  # , status='settled')
    project_payouts_aggregated = project_payouts.aggregate(Sum('amount_raised'), Sum('amount_payable'), Sum('organization_fee'))

    donations = data['donations'].filter(order__status='success')

    statistics.update(
        mydict(
            orders=mydict(
            total_amount=order_payments_aggregated['amount__sum'] or 0,
            transaction_fee=order_payments_aggregated['transaction_fee__sum'] or 0,
            count=order_payments.count()
            ),
            donations= mydict(
                total_amount=donations.aggregate(Sum('amount'))['amount__sum'],
                count=donations.count()
            ),
            bank=mylist(),
            docdata=mydict(
                payment=mydict(
                    total_amount=remote_docdata_payments_aggregated['amount_collected__sum'] or 0,
                    docdata_fee=remote_docdata_payments_aggregated['docdata_fee__sum'] or 0,
                    third_party=remote_docdata_payments_aggregated['tpci__sum'] or 0,
                    count=remote_docdata_payments.count()
                ),
                payout=mydict(
                    total_amount=remote_docdata_payouts_aggregated['payout_amount__sum'] or 0,
                    count=remote_docdata_payouts.count()
                ),
            ),
            project_payouts=mydict(
                per_payout_rule=project_payouts.order_by('payout_rule').values('payout_rule').annotate(
                    raised=Sum('amount_raised'),
                    payable=Sum('amount_payable'),
                    organization_fee=Sum('organization_fee'),
                    count=Count('payout_rule'),
                    ),
                raised=project_payouts_aggregated['amount_raised__sum'] or 0,
                payable=project_payouts_aggregated['amount_payable__sum'] or 0,
                organization_fee=project_payouts_aggregated['organization_fee__sum'] or 0,
                count=project_payouts.count()
            ),
        )
    )


    # Tpci (third party costs)
    # Tdf (docdata fee)

    bank_accounts = mydict(BANK_ACCOUNTS)

    for sender_account, name in bank_accounts.items():
        if sender_account:
            qs = bank_transactions.filter(sender_account=sender_account)
        else:
            qs = bank_transactions
            categories = mylist()

            for category in [None] + list(BankTransactionCategory.objects.all()):
                credit = qs.filter(category=category, credit_debit='C').aggregate(Sum('amount'))['amount__sum']
                debit = qs.filter(category=category, credit_debit='D').aggregate(Sum('amount'))['amount__sum']

                categories.append(mydict(
                        category=category,
                        credit=credit,
                        debit=debit,
                        balance=(credit or 0) - (debit or 0),
                        ))

                credit = qs.filter(credit_debit='C').aggregate(Sum('amount'))['amount__sum']
                debit = qs.filter(credit_debit='D').aggregate(Sum('amount'))['amount__sum']

                statistics['bank'].append(mydict(
                        per_category=categories,
                        account_number=sender_account,
                        name=name,
                        credit=credit,  # in
                        debit=debit,    # out
                        balance=(credit or 0 ) - (debit or 0),
                        count=qs.count(),
                ))

            statistics['docdata']['pending_orders'] = \
                statistics['orders']['total_amount'] - \
                statistics['docdata']['payout']['total_amount']

            statistics['docdata']['pending_service_fee'] = \
                statistics['orders']['transaction_fee'] - \
                statistics['docdata']['payment']['docdata_fee'] - \
                statistics['docdata']['payment']['third_party']

            statistics['docdata']['pending_payout'] = \
                statistics['docdata']['payment']['total_amount'] - \
                sum([entry['balance'] for entry in statistics['bank'][0]['per_category'] if entry['category'] and entry['category'].pk == 2])

            statistics['docdata']['payout']['other_costs'] = \
                statistics['docdata']['payment']['total_amount'] - \
                statistics['docdata']['payment']['docdata_fee'] - \
                statistics['docdata']['payment']['third_party'] - \
                statistics['docdata']['payout']['total_amount']
    return statistics
