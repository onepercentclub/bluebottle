from bluebottle.bb_orders.models import BaseOrder
from bluebottle.utils.utils import PreviousStatusMixin


class Order(BaseOrder, PreviousStatusMixin):
    @property
    def anonymous(self):
        return False if self.user else True

    @property
    def payment_message(self):
        # TODO: Use this for other PSP messages/errors too.
        # Now this only returns codes on payment level and only
        # Interswitch is using that, but later we might expand this.
        if self.order_payment.status_code:
            return {
                'code': self.order_payment.status_code,
                'description': self.order_payment.status_description
            }

    class Analytics:
        type = 'order'
        tags = {
            'id': 'id',
            'status': 'status',
            'anonymous': 'anonymous'
        }
        fields = {
            'id': 'id',
            'user_id': 'user.id'
        }

        @staticmethod
        def extra_tags(obj, created):
            return {'total_currency': str(obj.total.currency)}

        @staticmethod
        def extra_fields(obj, created):
            return {'total': float(obj.total)}

        @staticmethod
        def timestamp(obj, created):
            if created:
                return obj.created
            else:
                return obj.updated
