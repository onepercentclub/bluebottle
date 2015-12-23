from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime

from .models import BankTransaction, RemoteDocdataPayment, RemoteDocdataPayout, BankTransactionCategory, BankAccount
from decimal import Decimal


def add_up(first, second):
    """
    Addition of two objects.

    Distinguish addition of dictionaries, list and numbers.

    return None when both are None
    if one of the two is None, return the other one which is not None

    if both are mydicts, add them up with the custom mydict.__add__
    if both are mylists, add them up with the .add method

    if both are convertable to a Decimal, return the addition of the numbers

    in other cases, return None
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
        else:
            try:
                return Decimal(str(first)) + Decimal(str(second))
            except:
                return None


class mydict(dict):

    def __add__(self, dict2):
        if self == mydict():
            return dict2

        new_dict = mydict()

        keys = self.keys()
        if set(keys) != set(dict2.keys()):
            return new_dict

        for key in keys:
            new_dict[key] = add_up(self[key], dict2[key])

        return new_dict


class mylist(list):

    def add(self, list2):
        length = len(self)
        if length != len(list2):
            return mylist()

        return mylist([add_up(self[i], list2[i]) for i in range(length)])


def get_datefiltered_qs(start, stop):
    from bluebottle.donations.models import Donation
    from bluebottle.payments.models import OrderPayment
    from bluebottle.payouts.models import ProjectPayout

    data = mydict()
    data['transactions'] = BankTransaction.objects.filter(book_date__gte=start, book_date__lte=stop)
    data['order_payments'] = OrderPayment.objects.filter(created__gte=start, created__lte=stop)
    data['remote_docdata_payments'] = RemoteDocdataPayment.objects.filter(remote_payout__payout_date__gte=start,
                                                                          remote_payout__payout_date__lte=stop)
    data['remote_docdata_payouts'] = RemoteDocdataPayout.objects.filter(payout_date__gte=start, payout_date__lte=stop)

    # on this date there was an import of old data that should not appear in the statistics
    # excluded_date = timezone.datetime(2014, 7, 8)
    # data['project_payouts'] = ProjectPayout.objects.exclude(created__gte=excluded_date,
    #                                                         created__lt=excluded_date + timezone.timedelta(days=1))
    data['project_payouts'] = ProjectPayout.objects.all()
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
    # above item is not used anywhere, and does not make a lot of sense since it adds up both credit and debit transactions
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
    categories_list = [None] + list(BankTransactionCategory.objects.all())
    # BankTransactionCategory can differ per tenant. structure of the dict can be different,
    # when merging it can result in None

    for account in BankAccount.objects.all():
        if account.account_nr:
            qs = bank_transactions.filter(sender_account=account.account_nr)
        else:
            qs = bank_transactions

        categories = mylist()

        for category in categories_list:
            credit = qs.filter(category=category, credit_debit='C').aggregate(Sum('amount'))['amount__sum'] or 0
            debit = qs.filter(category=category, credit_debit='D').aggregate(Sum('amount'))['amount__sum'] or 0

            categories.append(mydict(
                    category=category,
                    credit=credit,
                    debit=debit,
                    balance=credit - debit,
                    ))

        credit = qs.filter(credit_debit='C').aggregate(Sum('amount'))['amount__sum'] or 0
        debit = qs.filter(credit_debit='D').aggregate(Sum('amount'))['amount__sum'] or 0

        statistics['bank'].append(mydict(
                per_category=categories,
                account_number=account.account_nr,
                name=account.account_name,
                credit=credit,  # in
                debit=debit,    # out
                balance=credit - debit,
                count=qs.count(),
        ))

        statistics['docdata']['pending_orders'] = statistics['orders']['total_amount'] - \
                                                  statistics['docdata']['payout']['total_amount']

        statistics['docdata']['pending_service_fee'] = statistics['orders']['transaction_fee'] - \
                                                       statistics['docdata']['payment']['docdata_fee'] - \
                                                       statistics['docdata']['payment']['third_party']

        # pending payout is the total amount of docdata payment MINUS sum of all banktransactions of category DocdataPayout
        # NOTE: this was matched by pk before, the line below makes clear that this should be the specific BankTransactionCategory 'Docdata payout'
        # TODO: BankTransactionCategory can be filled in admin and can be different for multiple tenants, so this should be improved
        dd_payout_category = BankTransactionCategory.objects.get(pk=2, name='Docdata payout')
        statistics['docdata']['pending_payout'] = statistics['docdata']['payment']['total_amount'] - \
                                                  sum([entry['balance'] for entry in statistics['bank'][0]['per_category'] if entry['category'] == dd_payout_category])

        statistics['docdata']['payout']['other_costs'] = statistics['docdata']['payment']['total_amount'] - \
                                                         statistics['docdata']['payment']['docdata_fee'] - \
                                                         statistics['docdata']['payment']['third_party'] - \
                                                         statistics['docdata']['payout']['total_amount']
    return statistics


def get_bank_account_info():
    """
    Only accounts that are in bluebottle.accounting.models.BankAccounts will be matched
    """
    bank_accounts = []
    for account in BankAccount.objects.all():
        if account.account_nr:
            transactions = BankTransaction.objects.filter(Q(sender_account=account.account_nr) | \
                                                          Q(counter_account=account.account_nr))
            credit_transactions = transactions.filter(credit_debit='C').order_by('-book_date')
            debit_transactions = transactions.filter(credit_debit='D').order_by('-book_date')
            credit_transaction = credit_transactions.first() if credit_transactions.exists() else None
            debit_transaction = debit_transactions.first() if debit_transactions.exists() else None

            # this block is needed to determine a correct link, filter on transactions
            # by either sender_account=account_nr or counter_account=account_nr
            credit_sender_counter = 'sender'
            if credit_transaction and credit_transaction.sender_account != account.account_nr:
                    credit_sender_counter = 'counter'

            debit_sender_counter = 'counter'
            if debit_transaction and debit_transaction.counter_account != account.account_nr:
                    debit_sender_counter = 'sender'

            bank_accounts.append({
                'account_name': account.account_name,
                'account_nr': account.account_nr,
                'last_credit_transaction_date': credit_transaction.book_date if credit_transaction else '',
                'last_credit_transaction_name': str(credit_transaction)[:40] if credit_transaction else '',
                'credit_sender_counter': credit_sender_counter,
                'debit_sender_counter': debit_sender_counter,
                'last_debit_transaction_date': debit_transaction.book_date if debit_transaction else '',
                'last_debit_transaction_name': str(debit_transaction)[:40] if debit_transaction else '',
                })

    return bank_accounts
