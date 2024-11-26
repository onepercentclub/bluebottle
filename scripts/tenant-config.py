
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from django.db import connection
from bluebottle.clients.utils import tenant_url
import requests

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from io import BytesIO
from django.core.files import File

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.mails.models import MailPlatformSettings
from bluebottle.clients import properties

FILE_HASH = '1730716553814'

def run(*args):
    for tenant in Client.objects.all().all():
        with LocalTenant(tenant):
            try:
                mail_settings = MailPlatformSettings.objects.get()

                mail_settings.address = properties.TENANT_MAIL_PROPERTIES.get('address')
                mail_settings.footer = properties.TENANT_MAIL_PROPERTIES.get('footer')
                mail_settings.sender = properties.TENANT_MAIL_PROPERTIES.get('sender')
                mail_settings.reply_to = properties.TENANT_MAIL_PROPERTIES.get('reply_to')

                mail_settings.save()
            except AttributeError as e:
                print(f'Failed to set mail settings for {tenant.client_name}', e)

            settings = SitePlatformSettings.objects.get()

            domain_url = f'https://{tenant.domain_url}'
            if 'localhost' in domain_url:
                domain_url = f'https://{tenant.client_name}.s.goodup.com'

            logo_url = f'{domain_url}/images/logo.svg'
            favicon_url = f'{domain_url}/images/favicons/android-chrome-192x192.png'
            favicon_small_url = f'{domain_url}/images/favicons/favicon-32x32.png'

            try:
                logo_response = requests.get(logo_url)
                logo_response.raise_for_status()

                settings.logo = File(BytesIO(logo_response.content))
                settings.logo.name = 'logo.svg'
            except Exception as e:
                print(f'failed to get logo for {tenant.client_name}, {logo_url}')

            try:
                favicon_response = requests.get(favicon_url)
                favicon_response.raise_for_status()

                settings.favicon = File(BytesIO(favicon_response.content))
                settings.favicon.name = 'favicon.png'
            except Exception as e:
                try:
                    favicon_response = requests.get(favicon_small_url)
                    favicon_response.raise_for_status()

                    settings.favicon = File(BytesIO(favicon_response.content))
                    settings.favicon.name = 'favicon.png'
                except:
                    print(f'failed to get favicon for {tenant.client_name}, {favicon_url}')

            settings.save()
