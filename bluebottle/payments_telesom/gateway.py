import hashlib

from suds.client import Client
from suds.plugin import MessagePlugin


class NameSpacePlugin(MessagePlugin):

    def sending(self, context):
        context.envelope = context.envelope.replace('ns0:', '')
        print context.envelope
        return context.envelope


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
        # self.client = Client(api_url + '?wsdl')
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key

    def create(self, account=None, amount=0, description=''):
        """
        Create the payment in Telesom.
        """
        payment = self.client.factory.create('PaymentRequest')
        payment.pMsisdn = account
        payment.pAmount = amount
        payment.Category = description
        payment.MerchantID = self.merchant_id
        ip = '213.127.165.114'
        id = 'ne-1'
        date = '13/02/2017'
        # subscriber + amount + account + description + Password + IPAddress + UniqueKey + date
        hashkey = hashlib.md5("{0}{1}{2}{3}{4}{5}{6}{7}".format(
            account, amount, self.merchant_id, description, self.merchant_key, ip, id, date
        ))
        payment.hashkey = hashkey.hexdigest()

        reply = self.client.service.PaymentRequest(payment)
        return reply
