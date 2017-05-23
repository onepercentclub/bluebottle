from bluebottle.bb_donations.models import BaseDonation
from bluebottle.utils.utils import StatusDefinition

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_donation', 'change_donation', 'delete_donation',
        )
    }
}


class Donation(BaseDonation):

    def __unicode__(self):
        return u'{} for {}'.format(self.amount, self.project)

    def get_payment_method(self):
        order_payment = self.order.get_latest_order_payment()
        if not order_payment:
            return '?'
        if order_payment.status == StatusDefinition.PLEDGED:
            return 'pledge'
        if not hasattr(order_payment, 'payment'):
            return '?'
        return order_payment.payment.method_name
