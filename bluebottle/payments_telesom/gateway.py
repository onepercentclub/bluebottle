import hashlib

from django.utils import timezone

import ipgetter
from suds.client import Client
from suds.plugin import MessagePlugin


class NameSpacePlugin(MessagePlugin):

    def sending(self, context):
        print context.envelope
        return context


class TelesomClient(object):
    """
    API Client for Telesom Zaad.

    This is a wrapper around the SOAP service methods,
    providing more Python-friendly wrappers.
    """
    def __init__(self, merchant_id, merchant_key, api_url):
        """
        Initialize the client.
        """
        self.client = Client(api_url + '?wsdl', plugins=[NameSpacePlugin()])
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key

    def create(self, subscriber=None, amount=0, description=''):
        """
        Create the payment in Telesom.
        """
        ip = ipgetter.myip()
        date = timezone.now().strftime('%d/%m/%Y')
        # username = 'shadir'
        password = 'ieu45fi33%334'
        key = '334fr43453423d'
        merchant = '400032'
        # key = subscriber + amount + account + description + Password + IPAddress + UniqueKey + date
        key = hashlib.md5("{0}{1}{2}{3}{4}{5}{6}{7}".format(
            subscriber, amount, merchant, description, password, ip, key, date
        )).hexdigest().upper()
        print subscriber, amount, merchant, description, password, ip, key, date
        reply = self.client.service.PaymentRequest(
            pMsisdn=subscriber,
            pAmount=amount,
            Category=description,
            MerchantID=self.merchant_id,
            hashkey=key
        )
        print reply
        return reply
