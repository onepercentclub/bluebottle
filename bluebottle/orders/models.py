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
            'amount': 'total'
        }


import signals  # noqa
