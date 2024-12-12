from django.core.mail import \
    EmailMultiAlternatives as BaseEmailMultiAlternatives

from bluebottle.mails.models import MailPlatformSettings


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
    settings = MailPlatformSettings.load()

    if not settings.address:
        return None

    return f"{settings.sender} <{settings.address}>"


class EmailMultiAlternatives(BaseEmailMultiAlternatives):
    """
    A tenant-aware emailer. Replaces the from_email by the tenant's
    address, if available
    """

    def __init__(self, from_email=None, headers=None, *args, **kwargs):
        if headers is None:
            headers = {}

        settings = MailPlatformSettings.load()

        if settings.reply_to:
            headers['Reply-To'] = settings.reply_to

        if not from_email:
            from_email = construct_from_header()

        super(EmailMultiAlternatives, self).__init__(from_email=from_email, headers=headers, *args, **kwargs)
