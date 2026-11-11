import factory

from bluebottle.members.models import (
    FacebookAuthentication, GoogleAuthentication, PasswordAuthentication, SAMLAuthentication
)
from bluebottle.test.factory_models.organizations import OrganizationFactory


class PasswordAuthenticationFactory(factory.DjangoModelFactory):
    class Meta():
        model = PasswordAuthentication

    enabled = True
    account_creation_rules = 'anyone'


class FacebookAuthenticationFactory(factory.DjangoModelFactory):
    class Meta():
        model = FacebookAuthentication

    enabled = True
    secret = 'facebook-secret'
    client_id = 'facebook-client-id'


class GoogleAuthenticationFactory(factory.DjangoModelFactory):
    class Meta():
        model = GoogleAuthentication

    enabled = True
    secret = 'google-secret'
    client_id = 'google-client-id'


class SAMLAuthenticationFactory(factory.DjangoModelFactory):
    class Meta():
        model = SAMLAuthentication

    enabled = True
    organization = factory.SubFactory(OrganizationFactory)

    entity_id = factory.Sequence(lambda n: f'https://idp{n}.example.com')
    local_entity_id = factory.Sequence(lambda n: f'https://sp{n}.example.com')
    certificate = 'certificate'
    single_sign_on_url = factory.Sequence(lambda n: f'https://idp{n}.example.com/sso')
    single_logout_url = factory.Sequence(lambda n: f'https://idp{n}.example.com/slo')
    name_id_format = 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'

    remote_id_attribute = 'uid'
    email_attribute = 'email'
    last_name_attribute = 'last_name'
    first_name_attribute = 'first_name'
    work_location_attribute = 'work_location'

    metadata_file = 'members/saml-metadata/metadata.xml'
