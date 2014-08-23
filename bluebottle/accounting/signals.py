from bluebottle.bb_payouts.choices import PayoutLineStatuses
from bluebottle.utils.model_dispatcher import get_project_payout_model

PROJECT_PAYOUT_MODEL = get_project_payout_model()


def match_transaction_with_payout(transaction):

    line = transaction.description1.split(' ')

    if len(line) > 0:
        invoice_reference = line[0]
        try:
            transaction.payout =  PROJECT_PAYOUT_MODEL.objects.get(invoice_reference=invoice_reference)
            transaction.category_id = 1
            transaction.save()
        except PROJECT_PAYOUT_MODEL.DoesNotExist:
            pass


def match_transaction_with_payout_on_creation(sender, instance, created, **kwargs):

    transaction = instance
    if not transaction.payout:

        match_transaction_with_payout(transaction)


def change_payout_status_with_matched_transaction(sender, instance, created, **kwargs):

    transaction = instance

    if transaction.payout:
        payout = transaction.payout
        payout.status = PayoutLineStatuses.completed
        payout.completed = transaction.book_date
        payout.save()
