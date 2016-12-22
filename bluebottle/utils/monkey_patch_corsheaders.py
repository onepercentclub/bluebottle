import corsheaders.defaults
from bluebottle.clients import properties

defaults = corsheaders.defaults


class TenantAwareCorsDefaults(object):
    def __getattr__(self, attr):
        try:
            return getattr(properties, attr)
        except AttributeError:
            return getattr(defaults, attr)


corsheaders.defaults = TenantAwareCorsDefaults()
