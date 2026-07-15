from datetime import datetime

from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.funding.models import Funding, Donor
from bluebottle.geo.mapbox import get_translated_geofeature_list, locality_from_geolocation
from bluebottle.initiatives.documents import deduplicate, get_translated_country_list

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
            impact_location = instance.impact_location
            country = impact_location.country
            geofeature = impact_location.geofeature
            locations.append({
                'id': impact_location.id,
                'name': (
                    geofeature.place_name if geofeature else impact_location.formatted_address
                ),
                'locality': locality_from_geolocation(impact_location),
                'country_code': country.alpha2_code if country else None,
                'country': country.name if country else None,
                'type': 'location'
            })
        elif instance.initiative and instance.initiative.place:
            place = instance.initiative.place
            country = place.country
            geofeature = place.geofeature
            locations.append({
                'id': place.id,
                'name': (
                    geofeature.place_name if geofeature else place.formatted_address
                ),
                'locality': locality_from_geolocation(place),
                'country_code': country.alpha2_code if country else None,
                'country': country.name if country else None,
                'type': 'impact_location',
            })
        return locations

    def prepare_geofeature(self, instance):
        if not instance.impact_location or instance.impact_location.geofeatures.count() == 0:
            return super().prepare_geofeature(instance)

        geofeatures = []
        location = instance.impact_location
        primary_id = location.geofeature_id
        country = location.country
        for geofeature in location.geofeatures.all():
            geofeatures = geofeatures + get_translated_geofeature_list(
                geofeature,
                country=country,
                is_primary=geofeature.pk == primary_id,
            )
        return geofeatures

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
            countries += get_translated_country_list(instance.impact_location.country)

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
