from django.core.mail import EmailMultiAlternatives as BaseEmailMultiAlternatives

from bluebottle.clients import properties

def construct_from_header():
    """
        construct a from header based on what's in 'properties'. Return
        None if no sender data (address) is available, which shoud result
        in the system default being used.
    """
    mail_address = properties.TENANT_MAIL_PROPERTIES.get('address')
    mail_name = properties.TENANT_MAIL_PROPERTIES.get('sender')
    if not mail_name:
        mail_name = properties.TENANT_MAIL_PROPERTIES.get('name')
    if not mail_name:
        mail_name = mail_address

    if not mail_address:
        return None

    return "{0} <{1}>".format(mail_name, mail_address)

class EmailMultiAlternatives(BaseEmailMultiAlternatives):
    """
    A tenant-aware emailer. Replaces the from_email by the tenant's
    address, if available
    """
    def __init__(self, from_email=None, *args, **kwargs):
        tenant_from = construct_from_header()
        if from_email is None and tenant_from:
            kwargs['from_email'] = tenant_from

        super(EmailMultiAlternatives, self).__init__(*args, **kwargs)

