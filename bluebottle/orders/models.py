from bluebottle.bb_orders.models import BaseOrder
from bluebottle.utils.utils import PreviousStatusMixin


class Order(BaseOrder, PreviousStatusMixin):
    @property
    def anonymous(self):
        return True if self.user else False

    class Analytics:
        type = 'order'
        tags = {
            'status': 'status',
            'anonymous': 'anonymous'
        }
        fields = {
            'id': 'id',
            'amount': 'total'
        }


import signals  # noqa
