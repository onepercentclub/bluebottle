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

    def __init__(self, merchant_id, merchant_key, username, password, api_domain):
        """
        Initialize the client.
        """
        self.client = Client(api_domain + '?WSDL', plugins=[NameSpacePlugin()])
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.username = username
        self.password = password
        self.testing = True
        if 'http://epayment.mytelesom.com/' in api_domain:
            self.testing = False

    def create(self, mobile='', amount=0, description=''):
        """
        Create the payment in Telesom.
        """
        # We should not use actual IP address.
        ip = '::1'
        date = timezone.now().strftime('%d/%m/%Y')
        username = self.username
        password = self.password
        account = self.merchant_id
        unique_key = self.merchant_key

        # From PHP:
        # $msg = $username.$password."::1".$merchant.$uniquekey. $dates.$mobile.$amount.$description;
        hash = "{0}{1}{2}{3}{4}{5}{6}{7}{8}".format(
            username, password, ip, account, unique_key, date, mobile, amount, description
        )
        key = hashlib.md5(hash).hexdigest()

        if self.testing:
            reply = self.client.service.PaymentRequest(
                pMsisdn=mobile,
                pAmount=amount,
                Category=description,
                MerchantID=self.merchant_id,
                hashkey=key
            )
        else:
            reply = self.client.service.PaymentRequest(
                Subscriber=mobile,
                Amount=amount,
                Account=self.merchant_id,
                Description=description,
                Key=key
            )

        # Requests (including typos, please leave as is)
        # ------------------
        # 2001! Success, Waiting Confirmation !100
        # 400!Error: connect ECONNREFUSED!
        # 400!Error: connect Unknown system errno 10056!
        # 4005! Insufficient Payer Account funds.!
        # 4005! Invalid Payee Account Info. !
        # 4005! Invalid Payee Account relation. !
        # 4005! OOPS ! , Sorry your request could not be complete this time !!
        # 4005! There is somthing got wrong, please try again !
        # 4005!!
        # 4005!Payer Account Does not Exist.!
        # 5000!Account Locked, You can Try again after 24 Hours!-1
        # 5001! Invalid Username/Password/Hashkey Try Again!-1
        # 5002!Error Occured Cannot Proccess Payment!-1
        # 5004!Authentication Error!-1

        res = reply.split('!')
        if res[0] == '2001':
            return {
                'response': reply,
                'status': 'created',
                'payment_id': res[2]
            }
        else:
            raise PaymentException("Could not start Telesom/Zaad transaction. {0}".format(reply))

    def check_status(self, payment_id):

        # We should not use actual IP address.
        ip = '::1'
        date = timezone.now().strftime('%d/%m/%Y')
        username = self.username
        password = self.password
        account = self.merchant_id
        unique_key = self.merchant_key

        # From PHP:
        # $msg =  $username.$password."::1".$merchant.$uniquekey.$dates.$paymentid;
        hash = "{0}{1}{2}{3}{4}{5}{6}".format(
            username, password, ip, account, unique_key, date, payment_id
        )
        key = hashlib.md5(hash).hexdigest()

        if self.testing:
            reply = self.client.service.ProcessPayment(
                MerchantID=self.merchant_id,
                Paymentid=payment_id,
                hashkey=key
            )
        else:
            reply = self.client.service.ProcessPayment(
                Account=self.merchant_id,
                PaymentNo=payment_id,
                Key=key
            )

        # Responses (including typos, please leave as is)
        # ----------------
        # 2001! Your account was Credited with $5.0000 Charge fee $ 0
        # 5004!Authentication Error!-1
        # 4005! Thi payment was processed
        # 6001! This payment is Rejected
        # 4005! This payment is Rejected
        # 5001! Invalid Transaction fee configuration.
        # 4005!Oops! Operation could not be completed, if this is permanent please contact support.
        # 5002!Error Occured Cannot Proccess Payment
        # 400!Error: connect Unknown system errno 10056
        # 3011! Thi payment was processed
        # 4005! Invalid Payment Claim
        # 4005! Invalid Transaction fee configuration.
        # 6002! This payment is not yet Approved
        # 4005! Invalid Payment Request Id
        # 4005! This payment is not yet Approved

        res = reply.split('!')
        if res[0] == '2001' or res[1] == ' This payment was processed ':
            status = 'settled'
        elif res[0] == '4005':
            status = 'started'
        else:
            status = 'failed'
        return {
            'response': reply,
            'status': status,
            'message': res[1]
        }
