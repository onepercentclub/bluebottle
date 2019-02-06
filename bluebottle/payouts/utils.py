from collections import defaultdict
from bluebottle.clients import properties


def get_payout_settings():
    result = defaultdict(list)
    if hasattr(properties, 'PAYOUT_METHODS'):
        for payout_method in properties.PAYOUT_METHODS:
            for currency in payout_method['currencies']:
                result[currency].append(payout_method['method'])

    return result
