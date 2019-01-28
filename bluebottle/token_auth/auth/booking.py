import base64
import hashlib
import hmac
import logging
import re
import urllib
from datetime import timedelta
import string
from datetime import datetime

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from Crypto import Random
from Crypto.Cipher import AES

from bluebottle.token_auth.models import CheckedToken
from bluebottle.token_auth.auth.base import BaseTokenAuthentication
from bluebottle.token_auth.exceptions import TokenAuthenticationError
from bluebottle.token_auth.utils import get_settings

logger = logging.getLogger(__name__)


def _encode_message(message):
    """
    Helper method which returns an encoded version of the
    message passed as an argument.
    It returns a tuple containing a string formed by two elements:
    1. A string formed by the initialization vector and the AES-128
    encrypted message.
    2. The HMAC-SHA1 hash of that string.
    """
    aes_key = get_settings()['aes_key']
    hmac_key = get_settings()['hmac_key']

    pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(
        AES.block_size - len(s) % AES.block_size)
    init_vector = Random.new().read(AES.block_size)
    cipher = AES.new(aes_key, AES.MODE_CBC, init_vector)
    padded_message = pad(message)
    aes_message = init_vector + cipher.encrypt(padded_message)
    hmac_digest = hmac.new(str(hmac_key), str(aes_message), hashlib.sha1)

    return aes_message, hmac_digest


def generate_token(email, username, first_name, last_name):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = 'time={0}|username={1}|name={2} {3}|' \
              'email={4}'.format(timestamp, username, first_name, last_name, email)
    aes_message, hmac_digest = _encode_message(message)
    token = base64.urlsafe_b64encode(aes_message + hmac_digest.digest())
    return token


class TokenAuthentication(BaseTokenAuthentication):
    """
    This authentication backend expects a token, encoded in URL-safe Base64, to
    be received from the user to be authenticated. The token must be built like
    this:

    - The first 16 bytes are the AES key to be used to decrypt the message.
    - The last 20 bytes are the HMAC-SHA1 signature of the message AND the AES
    key, to provide an extra safety layer on the process.
    - The rest of the token, between the first 16 bytes and the latest 20, is
    the encrypted message to be read.

    The backend performs the next operations over a received token in order to
    authenticate the user who is sending it:

    1. Checks that the token was not used previously, to prevent replay.
    2. Decodes it through Base64.
    3. Checks the HMAC-SHA1 signature of the message.
    4. Decrypts the AES-encoded message to read the data.
    5. Read the timestamp included in the message to check if the token already
    expired or if its finally valid.
    """
    def check_hmac_signature(self, message):
        """
        Checks the HMAC-SHA1 signature of the message.
        """
        data = message[:-20]
        checksum = message[-20:]
        hmac_data = hmac.new(str(self.settings['hmac_key']), str(data), hashlib.sha1)

        return True if hmac_data.digest() == checksum else False

    def get_login_data(self, data):
        """
        Obtains the data from the decoded message. Returns a Python tuple
        of 4 elements containing the login data. The elements, from zero
        to three, are:

        0. Timestamp.
        1. Username.
        2. Complete name.
        3. Email.
        """
        expression = r'(.*?)\|'
        pattern = r'time={0}username={0}name={0}email=(.*)'.format(expression)
        login_data = re.search(pattern, data)

        return login_data.groups()

    def check_timestamp(self, data):
        timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
        time_limit = datetime.now() - \
            timedelta(seconds=self.settings['token_expiration'])
        if timestamp < time_limit:
            raise TokenAuthenticationError('Authentication token expired')

    def check_token_used(self):
        if not self.args.get('token'):
            raise TokenAuthenticationError(value='No token provided')
        try:
            CheckedToken.objects.get(token=self.args['token'])
            raise TokenAuthenticationError(
                value='Token was already used and is not valid')
        except CheckedToken.DoesNotExist:
            # Token was not used previously. Continue with auth process.
            pass

    def decrypt_message(self):
        """
        Decrypts the AES encoded message.
        """
        token = str(self.args['token'])
        message = base64.urlsafe_b64decode(token)

        # Check that the message is valid (HMAC-SHA1 checking).
        if not self.check_hmac_signature(message):
            raise TokenAuthenticationError('HMAC authentication failed')

        init_vector = message[:16]
        enc_message = message[16:-20]

        aes = AES.new(self.settings['aes_key'], AES.MODE_CBC, init_vector)
        message = aes.decrypt(enc_message)

        # Get the login data in an easy-to-use tuple.
        try:
            login_data = self.get_login_data(message)
        except AttributeError:
            # Regex failed, so data was not valid.
            raise TokenAuthenticationError('Message does not contain valid login data')

        name = login_data[2].strip()
        first_name = name.split(' ').pop(0)
        parts = name.split(' ')
        parts.pop(0)
        last_name = " ".join(parts)
        email = login_data[3].strip()
        email = filter(lambda x: x in string.printable, email)

        data = {
            'timestamp': login_data[0],
            'remote_id': email,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'username': email
        }

        return data

    def get_metadata(self):
        metadata = "<sso-url>{0}</sso-url>".format(self.sso_url())
        return metadata

    def sso_url(self, target_url=None):
        url = self.settings['sso_url']
        if target_url:
            url += '?{}'.format(urllib.urlencode({'url': target_url.encode('utf-8')}))

        return url

    @property
    def target_url(self):
        return self.args['link']

    def authenticate_request(self):
        self.check_token_used()
        data = self.decrypt_message()
        self.check_timestamp(data)

        return data

    def finalize(self, user, data):
        timestamp = timezone.make_aware(parse_datetime(data['timestamp']))

        CheckedToken.objects.create(token=self.args['token'], user=user,
                                    timestamp=timestamp).save()
