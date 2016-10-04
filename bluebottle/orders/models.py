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
            # Handle future introduction of currency field for total
            try:
                return {'total_currency': obj.total_currency}
            except AttributeError:
                return {'total_currency': 'EUR'}

        def extra_fields(self, obj, created):
            # Force the total to a float. We don't currently have floats for 
            # order totals but in the future we may and Influxdb won't accept 
            # a later change in the type for a field.
            return {'total': float(obj.total)}


import signals  # noqa
