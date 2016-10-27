from bluebottle.bb_orders.models import BaseOrder
from bluebottle.utils.utils import PreviousStatusMixin


class Order(BaseOrder, PreviousStatusMixin):
    @property
    def anonymous(self):
        return False if self.user else True

    class Analytics:
        type = 'order'
        tags = {
            'status': 'status',
            'anonymous': 'anonymous'
        }
        fields = {
            'id': 'id',
            'user_id': 'user.id'
        }

        def extra_tags(self, obj, created):
            return {'total_currency': str(obj.total.currency)}

        def extra_fields(self, obj, created):
            return {'total': float(obj.total)}


import signals  # noqa
