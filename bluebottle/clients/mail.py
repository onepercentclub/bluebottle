from django.core.mail import EmailMultiAlternatives as BaseEmailMultiAlternatives

from bluebottle.clients import properties

class EmailMultiAlternatives(BaseEmailMultiAlternatives):
    """
    A tenant-aware emailer. Replaces the from_email by the tenant's
    address, if available
    """
    def __init__(self, from_email=None, *args, **kwargs):
        tenant_from = properties.TENANT_MAIL_PROPERTIES.get('sender')
        if from_email is None and tenant_from:
            kwargs['from_email'] = tenant_from

        super(EmailMultiAlternatives, self).__init__(*args, **kwargs)


