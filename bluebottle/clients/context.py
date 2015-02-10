from django.template import Context
from bluebottle.clients import properties

class ClientContext(Context):
    """
    A Context with builtin properties support. Mostly meant
    for rendering mail templates that don't get the
    ContextProcessor goodness
    """
    def __init__(self, *args, **kw):
        super(ClientContext, self).__init__(*args, **kw)
        try:
            self.update({
                'tenant_mail_properties':properties.TENANT_MAIL_PROPERTIES
            })
        except AttributeError:
            pass
