from mixpanel import Mixpanel
from bluebottle.clients import properties


def bb_track(title="", data={}):
    """
        Wrapper function for backend mixpanel tracking.
        One day we may be able to refactor this to the adapter pattern for
        multiple metrics.
    """
    if not title:
        return False

    mp = None
    key = getattr(properties, 'MIXPANEL', None)

    if key:
        mp = Mixpanel(key)
    else:
        return False

    if mp:
        mp.track(None, title, data)
