from builtins import str
from django_elasticsearch_dsl import Document, fields

from bluebottle.funding.models import Donor
from bluebottle.utils.documents import MultiTenantIndex
from bluebottle.activities.models import Activity
from bluebottle.utils.search import Search
from elasticsearch_dsl.field import DateRange


class DateRangeField(fields.DEDField, DateRange):
    pass


# The name of your index
activity = MultiTenantIndex('activity')
# See Elasticsearch Indices API reference for available settings
activity.settings(
    number_of_shards=1,
    number_of_replicas=0
)


class ActivityDocument(Document):
    title_keyword = fields.KeywordField(attr='title')
    title = fields.TextField(fielddata=True)
    slug = fields.KeywordField()
    description = fields.TextField()
    status = fields.KeywordField()
    status_score = fields.FloatField()
    created = fields.DateField()

    type = fields.KeywordField()

    image = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'type': fields.KeywordField(),
        'name': fields.KeywordField(),
    })

    owner = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': fields.TextField()
    })

    initiative = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'title': fields.TextField(),
        'pitch': fields.TextField(),
        'story': fields.TextField(),
    })

    theme = fields.NestedField(
        attr='initiative.theme',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    categories = fields.NestedField(
        attr='initiative.categories',
        properties={
            'id': fields.KeywordField(),
            'slug': fields.KeywordField(),
        }
    )
    position = fields.GeoPointField()

    country = fields.KeywordField()

    expertise = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    segments = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'type': fields.KeywordField(attr='segment_type.slug'),
            'name': fields.TextField(),
            'closed': fields.BooleanField(),
        }
    )

    is_online = fields.BooleanField()
    team_activity = fields.KeywordField()

    location = fields.NestedField(
        attr='location',
        properties={
            'id': fields.LongField(),
            'name': fields.TextField(),
            'city': fields.TextField(),
            'country': fields.TextField(attr='country.name'),
            'country_code': fields.TextField(attr='country.alpha2_code'),
        }
    )
    location_string = fields.TextField()

    contributors = fields.DateField()
    contributor_count = fields.IntegerField()
    donation_count = fields.IntegerField()

    start = fields.DateField()
    end = fields.DateField()

    duration = DateRangeField()
    activity_date = fields.DateField()

    class Django:
        model = Activity

    date_field = None

    def get_queryset(self):
        return super(ActivityDocument, self).get_queryset().select_related(
            'initiative', 'owner'
        ).prefetch_related(
            'contributors'
        )

    @classmethod
    def search(cls, using=None, index=None):
        # Use search class that supports polymorphic models
        return Search(
            using=using or cls._doc_type.using,
            index=index or cls._doc_type.index,
            doc_type=[cls],
            model=cls._doc_type.model
        )

    def prepare_image(self, instance):
        if instance.image:
            return {
                'id': instance.pk,
                'file': instance.image.file.name,
                'type': 'activity'
            }
        elif instance.initiative.image:
            return {
                'id': instance.initiative.pk,
                'file': instance.initiative.image.file.name,
                'type': 'initiative'
            }

    def prepare_contributors(self, instance):
        return [
            contributor.created for contributor
            in instance.contributors.filter(status__in=('succeeded', 'accepted'))
        ]

    def prepare_contributor_count(self, instance):
        return instance.contributors.filter(status__in=('succeeded', 'accepted')).count()

    def prepare_donation_count(self, instance):
        return instance.contributors.instance_of(Donor).filter(status='succeeded').count()

    def prepare_type(self, instance):
        return str(instance.__class__.__name__.lower())

    def prepare_country(self, instance):
        country_ids = []
        if instance.initiative.location:
            country_ids.append(instance.initiative.location.country_id)
        if hasattr(instance, 'office_location') and instance.office_location:
            country_ids.append(instance.office_location.country_id)
        if instance.initiative.place:
            country_ids.append(instance.initiative.place.country_id)
        return country_ids

    def prepare_location_string(self, instance):

        def location_to_string(location):
            if location.country and location.locality:
                return location.locality + ', ' + location.country.alpha2_code
            if location.country:
                return location.country.name
            return location.locality

        def office_to_string(office):
            return office.name

        if hasattr(instance, 'location') and instance.location:
            return location_to_string(instance.location)
        elif instance.initiative.place:
            return location_to_string(instance.initiative.place)
        elif hasattr(instance, 'office_location') and instance.office_location:
            return office_to_string(instance.office_location)
        elif instance.initiative.location:
            return office_to_string(instance.initiative.location)

    def prepare_location(self, instance):
        locations = []
        if hasattr(instance, 'location') and instance.location:
            if instance.location.country:
                locations.append({
                    'name': instance.location.formatted_address,
                    'city': instance.location.locality,
                    'country_code': instance.location.country.alpha2_code,
                    'country': instance.location.country.name
                })
            else:
                locations.append({
                    'name': instance.location.formatted_address,
                    'city': instance.location.locality,
                })
        if hasattr(instance, 'office_location') and instance.office_location:
            if instance.office_location.country:
                locations.append({
                    'id': instance.office_location.pk,
                    'name': instance.office_location.name,
                    'city': instance.office_location.city,
                    'country_code': instance.office_location.country.alpha2_code,
                    'country': instance.office_location.country.name
                })
            else:
                locations.append({
                    'id': instance.office_location.pk,
                    'name': instance.office_location.name,
                    'city': instance.office_location.city,
                })
        if instance.initiative.location:
            if instance.initiative.location.country:
                locations.append({
                    'id': instance.initiative.location.pk,
                    'name': instance.initiative.location.name,
                    'city': instance.initiative.location.city,
                    'country_code': instance.initiative.location.country.alpha2_code,
                    'country': instance.initiative.location.country.name
                })
            else:
                locations.append({
                    'id': instance.initiative.location.pk,
                    'name': instance.initiative.location.name,
                    'city': instance.initiative.location.city,
                })
        return locations

    def prepare_expertise(self, instance):
        if hasattr(instance, 'expertise') and instance.expertise:
            return {'id': instance.expertise_id}

    def prepare_is_online(self, instance):
        if hasattr(instance, 'is_online'):
            return instance.is_online

    def prepare_position(self, instance):
        return []

    def prepare_end(self, instance):
        return []

    def prepare_start(self, instance):
        return []
