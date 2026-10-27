from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.grant_management.models import GrantApplication, GrantDonor

SCORE_MAP = {
    'open': 1,
    'on_hold': 0.6,
    'succeeded': 0.5,
    'partially_funded': 0.5,
    'granted': 0.5,
    'refundend': 0.3,
}


@registry.register_document
@activity.doc_type
class GrantApplicationDocument(ActivityDocument):
    participant_class = GrantApplication

    def prepare_contribution_duration(self, instance):
        if instance.duration:
            return [
                {
                    'period': 'once',
                    'value': instance.duration.seconds / (60 * 60) + instance.duration.days * 24
                }
            ]

    class Django:
        related_models = ActivityDocument.Django.related_models + (GrantDonor,)
        model = GrantApplication

    def prepare_position(self, instance):
        return []

    def prepare_start(self, instance):
        return [None]

    def prepare_end(self, instance):
        return [None]

    def prepare_dates(self, instance):
        return [{
            'start': None,
            'end': None
        }]

    def prepare_duration(self, instance):
        return {"gte": None, "lte": None}

    def prepare_amount(self, amount):
        if amount:
            return {'amount': amount.amount, 'currency': str(amount.currency)}

    def prepare_target(self, instance):
        return self.prepare_amount(instance.target)

    def prepare_amount_raised(self, instance):
        return self.prepare_amount(instance.amount_granted)

    def prepare_is_online(self, instance):
        return True
