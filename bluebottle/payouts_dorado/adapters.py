from bluebottle.clients import properties


class DoradoPayoutAdapter(object):

    def __init__(self, project):
        self.settings = getattr(properties, 'PAYOUT_SERVICE', False)
        self.project = project
        
    def _get_update_url(self):
        return self.settings.url

    def trigger(self):
        
