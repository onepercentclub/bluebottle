from cryptography import x509
from cryptography.hazmat.backends import default_backend

from bluebottle.clients import properties
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant


def run(*args):
    for client in Client.objects.all():
        with LocalTenant(client):
            try:
                cert_string = '-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----'.format(
                    properties.TOKEN_AUTH['sp']['x509cert']
                )

                cert = x509.load_pem_x509_certificate(bytes(cert_string), default_backend())
                print('Our cert', client.name, cert.not_valid_after)
            except (AttributeError, KeyError):
                pass
            except Exception as e:
                print(e)

            try:
                cert_string = '-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----'.format(
                    properties.TOKEN_AUTH['idp']['x509cert']
                )

                cert = x509.load_pem_x509_certificate(bytes(cert_string), default_backend())
                print('Their cert', client.name, cert.not_valid_after)
            except (AttributeError, KeyError) as e:
                print(e)
            except Exception as e:
                print(e)
