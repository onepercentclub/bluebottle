from django.core.mail import EmailMultiAlternatives as BaseEmailMultiAlternatives

from bluebottle.clients import properties

class EmailMultiAlternatives(BaseEmailMultiAlternatives):
    """
    A tenant-aware emailer. Replaces the from_email by the tenant's
    address, if available
    """
    def __init__(self, from_email=None, *args, **kwargs):
        mail_address = properties.TENANT_MAIL_PROPERTIES.get('address')
        mail_name = properties.TENANT_MAIL_PROPERTIES.get('name')
        tenant_from = " {0} <{1}>".format(mail_name, mail_address)
        if from_email is None and tenant_from:
            kwargs['from_email'] = tenant_from

        super(EmailMultiAlternatives, self).__init__(*args, **kwargs)

