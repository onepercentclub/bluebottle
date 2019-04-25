from django.core.mail import \
    EmailMultiAlternatives as BaseEmailMultiAlternatives

from bluebottle.clients import properties


def construct_from_header():
    """
        construct a from header based on what's in 'properties'. Return
        None if no sender data (address) is available, which shoud result
        in the system default being used.
    """

    # The tenant properties will not be set if the call to this method
    # does not come via a django request => we need to setup the tenant
    # properties first.
    # properties.tenant_properties will be an empty dict if the tenant
    # properties has not be initialised yet.
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

    def __init__(self, from_email=None, headers=None, *args, **kwargs):
        if headers is None:
            headers = {}

        return_path = properties.TENANT_MAIL_PROPERTIES.get('return_path')
        if return_path:
            headers['Return-Path'] = return_path

        if not from_email:
            from_email = construct_from_header()

        super(EmailMultiAlternatives, self).__init__(from_email=from_email, headers=headers, *args, **kwargs)
