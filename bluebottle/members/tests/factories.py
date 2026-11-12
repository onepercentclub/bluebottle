import factory
from django.core.files.base import ContentFile

from bluebottle.members.models import (
    FacebookAuthentication, GoogleAuthentication, PasswordAuthentication, SAMLAuthentication
)
from bluebottle.test.factory_models.organizations import OrganizationFactory


class SingletonAuthenticationFactory(factory.DjangoModelFactory):
    """
    Authentication methods other than SAML can only exist once. Instead of
    creating a second instance (which violates the unique constraint), update
    the existing one with the given attributes.
    """
    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = model_class.objects.first()
        if instance is None:
            return super()._create(model_class, *args, **kwargs)

        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class PasswordAuthenticationFactory(SingletonAuthenticationFactory):
    class Meta():
        model = PasswordAuthentication

    enabled = True
    account_creation_rules = 'anyone'


class FacebookAuthenticationFactory(SingletonAuthenticationFactory):
    class Meta():
        model = FacebookAuthentication

    enabled = True
    secret = 'facebook-secret'
    client_id = 'facebook-client-id'


class GoogleAuthenticationFactory(SingletonAuthenticationFactory):
    class Meta():
        model = GoogleAuthentication

    enabled = True
    secret = 'google-secret'
    client_id = 'google-client-id'


IDP_CERTIFICATE = (
    "MIICgTCCAeoCCQCbOlrWDdX7FTANBgkqhkiG9w0BAQUFADCBhDELMAkGA1UEBhMCTk"
    "8xGDAWBgNVBAgTD0FuZHJlYXMgU29sYmVyZzEMMAoGA1UEBxMDRm9vMRAwDgYDVQQK"
    "EwdVTklORVRUMRgwFgYDVQQDEw9mZWlkZS5lcmxhbmcubm8xITAfBgkqhkiG9w0BCQ"
    "EWEmFuZHJlYXNAdW5pbmV0dC5ubzAeFw0wNzA2MTUxMjAxMzVaFw0wNzA4MTQxMjAx"
    "MzVaMIGEMQswCQYDVQQGEwJOTzEYMBYGA1UECBMPQW5kcmVhcyBTb2xiZXJnMQwwCg"
    "YDVQQHEwNGb28xEDAOBgNVBAoTB1VOSU5FVFQxGDAWBgNVBAMTD2ZlaWRlLmVybGFu"
    "Zy5ubzEhMB8GCSqGSIb3DQEJARYSYW5kcmVhc0B1bmluZXR0Lm5vMIGfMA0GCSqGSI"
    "b3DQEBAQUAA4GNADCBiQKBgQDivbhR7P516x/S3BqKxupQe0LONoliupiBOesCO3SH"
    "bDrl3+q9IbfnfmE04rNuMcPsIxB161TdDpIesLCn7c8aPHISKOtPlAeTZSnb8QAu7a"
    "RjZq3+PbrP5uW3TcfCGPtKTytHOge/OlJbo078dVhXQ14d1EDwXJW1rRXuUt4C8QID"
    "AQABMA0GCSqGSIb3DQEBBQUAA4GBACDVfp86HObqY+e8BUoWQ9+VMQx1ASDohBjwOs"
    "g2WykUqRXF+dLfcUH9dWR63CtZIKFDbStNomPnQz7nbK+onygwBspVEbnHuUihZq3Z"
    "UdmumQqCw4Uvs/1Uvq3orOo/WJVhTyvLgFVK2QarQ4/67OZfHd7R+POBXhophSMv1ZOo"
)


IDP_METADATA_TEMPLATE = """<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{entity_id}">
    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:KeyDescriptor use="signing">
            <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                <ds:X509Data>
                    <ds:X509Certificate>{certificate}</ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </md:KeyDescriptor>
        <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                                Location="{single_logout_url}"/>
        <md:NameIDFormat>{name_id_format}</md:NameIDFormat>
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                                Location="{single_sign_on_url}"/>
    </md:IDPSSODescriptor>
</md:EntityDescriptor>
"""


def build_idp_metadata(saml):
    return ContentFile(
        IDP_METADATA_TEMPLATE.format(
            entity_id=saml.entity_id,
            certificate=saml.certificate,
            single_sign_on_url=saml.single_sign_on_url,
            single_logout_url=saml.single_logout_url,
            name_id_format=saml.name_id_format,
        ).encode(),
        name='metadata.xml'
    )


class SAMLAuthenticationFactory(factory.DjangoModelFactory):
    class Meta():
        model = SAMLAuthentication

    class Params:
        # Not model fields: only used to build the IdP metadata file
        certificate = IDP_CERTIFICATE
        single_sign_on_url = factory.Sequence(lambda n: f'https://idp{n}.example.com/sso')
        single_logout_url = factory.Sequence(lambda n: f'https://idp{n}.example.com/slo')
        name_id_format = 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'

    enabled = True
    organization = factory.SubFactory(OrganizationFactory)

    entity_id = factory.Sequence(lambda n: f'https://idp{n}.example.com')

    remote_id_attribute = 'uid'
    email_attribute = 'email'
    last_name_attribute = 'last_name'
    first_name_attribute = 'first_name'
    work_location_attribute = 'work_location'

    metadata_file = factory.LazyAttribute(build_idp_metadata)
