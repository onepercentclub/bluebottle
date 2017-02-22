import hashlib

from bluebottle.payments.exception import PaymentException
from django.utils import timezone

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
    def __init__(self, merchant_id, merchant_key, username, password, api_url):
        """
        Initialize the client.
        """
        self.client = Client(api_url + '?WSDL', plugins=[NameSpacePlugin()])
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.username = username
        self.password = password

    def create(self, mobile='', amount=0, description=''):
        """
        Create the payment in Telesom.
        """
        # We should not use actual IP address.
        ip = '::1'
        date = timezone.now().strftime('%d/%m/%Y')
        username = self.username
        password = self.password
        uniquekey = self.merchant_id
        account = self.merchant_key

        # From PHP:
        # $msg = $username.$password."::1".$merchant.$uniquekey. $dates.$mobile.$amount.$description;
        hash = "{0}{1}{2}{3}{4}{5}{6}{7}{8}".format(
            username, password, ip, account, uniquekey, date, mobile, amount, description
        )
        key = hashlib.md5(hash).hexdigest()
        reply = self.client.service.PaymentRequest(
            pMsisdn=mobile,
            pAmount=amount,
            Category=description,
            MerchantID=self.merchant_id,
            hashkey=key
        )

        # 5001! Invalid Username/Password/Hashkey Try Again!-1
        # 2001! Success, Waiting Confirmation !265

        res = reply.split('!')
        if res[0] == '2001':
            return res[2]
        else:
            raise PaymentException(res[1])
