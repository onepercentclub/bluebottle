from datetime import datetime

from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.funding.models import Funding, Donor
from bluebottle.initiatives.documents import deduplicate, get_translated_list

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
class FundingDocument(ActivityDocument):
    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })
    amount_raised = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    class Django:
        model = Funding
        related_models = ActivityDocument.Django.related_models + (Donor, )

    def get_instances_from_related(self, related_instance):
        result = super().get_instances_from_related(related_instance)

        if result is not None:
            return result

        if isinstance(related_instance, Donor):
            return Funding.objects.filter(contributors=related_instance)

    def prepare_location(self, instance):
        locations = []
        if hasattr(instance, 'impact_location') and instance.impact_location:
            locations.append({
                'id': instance.impact_location.id,
                'name': instance.impact_location.formatted_address,
                'locality': instance.impact_location.locality,
                'country_code': instance.impact_location.country.alpha2_code,
                'country': instance.impact_location.country.name,
                'type': 'location'
            })
        elif instance.initiative and instance.initiative.place:
            if instance.initiative.place.country:
                locations.append({
                    'locality': instance.initiative.place.locality,
                    'country_code': instance.initiative.place.country.alpha2_code,
                    'country': instance.initiative.place.country.name,
                    'type': 'impact_location'
                })
            else:
                locations.append({
                    'locality': instance.initiative.place.locality,
                    'type': 'impact_location'
                })
        return locations

    def prepare_position(self, instance):
        positions = []
        if hasattr(instance, 'impact_location') and instance.impact_location and instance.impact_location.position:
            positions.append(
                {'lat': instance.impact_location.position.y, 'lon': instance.impact_location.position.x}
            )
        if instance.initiative and instance.initiative.place:
            positions.append(
                {'lat': instance.initiative.place.position.y, 'lon': instance.initiative.place.position.x}
            )
        return positions

    def prepare_country(self, instance):
        countries = super().prepare_country(instance)
        if instance.impact_location and instance.impact_location.country:
            countries += get_translated_list(instance.impact_location.country)

        return deduplicate(countries)

    def prepare_status_score(self, instance):
        return SCORE_MAP.get(instance.status, 0)

    def prepare_end(self, instance):
        return [instance.deadline]

    def prepare_dates(self, instance):
        return [{
            'start': datetime.min,
            'end': instance.deadline
        }]

    def prepare_duration(self, instance):
        if instance.started and instance.deadline and instance.started > instance.deadline:
            return {}
        return {'gte': instance.started, 'lte': instance.deadline}

    def prepare_amount(self, amount):
        if amount:
            return {'amount': amount.amount, 'currency': str(amount.currency)}

    def prepare_target(self, instance):
        return self.prepare_amount(instance.target)

    def prepare_amount_raised(self, instance):
        return self.prepare_amount(instance.amount_raised)

    def prepare_is_online(self, instance):
        if instance.impact_location:
            return False
        if instance.initiative and instance.initiative.place:
            return False
        return True
