from bluebottle.clients import properties


def get_flutterwave_settings():
    for account in properties.MERCHANT_ACCOUNTS:
        if account['merchant'] == 'flutterwave':
            return {'pub_key': account['pub_key']}
