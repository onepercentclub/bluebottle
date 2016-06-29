# Either import these settings in your base.py or write your own.

INTERSWITCH_PAYMENT_METHODS = (
    {
        'provider': 'interswitch',
        'id': 'interswitch-webpay',
        'profile': 'webpay',
        'name': 'WebPay',
        'supports_recurring': False,
    }
)


INTERSWITCH_PRODUCT_ID = 4220
INTERSWITCH_ITEM_ID = 101
INTERSWITCH_HASHKEY = '199F6031F20C63C18E2DC6F9CBA7689137661A05ADD4114ED10F5AFB64BE625B6A9993A634F590B64887EEB93FCFECB513EF9DE1C0B53FA33D287221D75643AB'
INTERSWITCH_PAYMENT_URL = 'https://stageserv.interswitchng.com/test_paydirect/pay'
INTERSWITCH_STATUS_URL = 'https://stageserv.interswitchng.com/test_paydirect/api/v1/gettransaction.json'