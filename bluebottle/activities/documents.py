from builtins import str

from django_elasticsearch_dsl import Document, fields
from elasticsearch_dsl.field import DateRange

from bluebottle.activities.models import Activity
from bluebottle.clients.utils import tenant_url
from bluebottle.funding.models import Donor
from bluebottle.geo.models import Location
from bluebottle.initiatives.documents import deduplicate, get_translated_list, get_translated_segments
from bluebottle.initiatives.models import Initiative, Theme
from bluebottle.segments.models import Segment
from bluebottle.utils.documents import MultiTenantIndex, TextField
from bluebottle.segments.models import Segment
from bluebottle.utils.search import Search


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
    title = TextField(fielddata=True)
    slug = fields.KeywordField()
    description = TextField(attr='description.html')
    highlight = fields.BooleanField()
    is_upcoming = fields.BooleanField()
    status = fields.KeywordField()
    created = fields.DateField()

    type = fields.KeywordField()
    resource_name = fields.KeywordField()
    manager = fields.KeywordField()
    link = fields.KeywordField()
    is_local = fields.BooleanField()

    def get_queryset(self):
        return super(ActivityDocument, self).get_queryset().select_related(
            'initiative',
            'owner',
            'image',
            'initiative__owner',
            'office_location',
            'office_location__country',
            'office_location__subregion',
            'office_location__subregion__region',
        ).prefetch_related(
            'segments',
            'segments__segment_type',
            'initiative__categories',
            'initiative__activity_managers',
            'contributors',
        )

    def get_indexing_queryset(self):
        return self.get_queryset()

    def prepare_link(self, instance):
        return None

    def prepare_is_local(self, instance):
        return True

    current_status = fields.NestedField(properties={
        'name': fields.KeywordField(),
        'label': fields.KeywordField(),
        'description': fields.KeywordField(),
    })

    image = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'type': fields.KeywordField(),
        'name': fields.KeywordField(),
    })

    owner = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'full_name': TextField()
    })

    initiative = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'title': TextField(),
        'pitch': TextField(),
        'story': TextField(attr='story.html'),
        'owner': fields.KeywordField(attr='owner.id'),
        'activity_managers': fields.NestedField(
            properties={
                'id': fields.KeywordField(),
            }
        )
    })

    theme = fields.NestedField(
        attr='theme',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
            'language': fields.KeywordField(),
        }
    )

    categories = fields.NestedField(
        attr='categories',
        properties={
            'id': fields.KeywordField(),
            'title': fields.KeywordField(),
            'language': fields.KeywordField()
        }
    )
    position = fields.GeoPointField()

    country = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
            'language': fields.KeywordField(),
        }
    )

    expertise = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
            'language': fields.KeywordField(),
        }
    )

    segments = fields.NestedField(
        properties={
            'id': fields.KeywordField(),
            'type': fields.KeywordField(attr='segment_type.slug'),
            'name': fields.KeywordField(),
            'closed': fields.BooleanField(),
            'language': fields.KeywordField(),
        }
    )

    is_online = fields.BooleanField()
    team_activity = fields.KeywordField()

    location = fields.NestedField(
        attr='location',
        properties={
            'id': fields.LongField(),
            'name': TextField(),
            'city': TextField(),
            'country': TextField(attr='country.name'),
            'country_code': TextField(attr='country.alpha2_code'),
        }
    )

    host_organization = fields.NestedField(
        attr='host_organization',
        properties={
            'id': fields.LongField(),
            'name': fields.TextField(),
            'logo': fields.TextField(),
        }
    )

    office = fields.NestedField(
        attr='office_location',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    office_subregion = fields.NestedField(
        attr='office_location.subregion',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    office_region = fields.NestedField(
        attr='office_location.subregion.region',
        properties={
            'id': fields.KeywordField(),
            'name': fields.KeywordField(),
        }
    )

    office_restriction = fields.NestedField(
        attr='office_restriction',
        properties={
            'restriction': TextField(),
            'office': fields.LongField(),
            'office_subregion': fields.LongField(),
            'office_region': fields.LongField(),
        }
    )

    contributors = fields.KeywordField()
    contributor_count = fields.IntegerField(attr='succeeded_contributor_count')
    capacity = fields.IntegerField()
    donation_count = fields.IntegerField()
    activity_type = fields.KeywordField()

    start = fields.DateField()
    end = fields.DateField()

    dates = fields.NestedField(
        properties={
            'start': fields.DateField(),
            'end': fields.DateField(),
        }
    )

    duration = DateRangeField()
    activity_date = fields.DateField()

    def get_instances_from_related(self, related_instance):
        model = self.Django.model

        if isinstance(related_instance, Initiative):
            return model.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Theme):
            return model.objects.filter(initiative__theme=related_instance)
        if isinstance(related_instance, Segment):
            return model.objects.filter(segments=related_instance)
        if isinstance(related_instance, Location):
            return model.objects.filter(office_location=related_instance)
        if isinstance(related_instance, Theme.translations.field.model):
            return model.objects.filter(initiative__theme=related_instance.master)

    class Django:
        related_models = (
            Initiative, Theme, Theme.translations.field.model, Segment, Location
        )
        model = Activity

    date_field = None

    @classmethod
    def search(cls, using=None, index=None):
        # Use search class that supports polymorphic models
        return Search(
            using=using or cls._doc_type.using,
            index=index or cls._doc_type.index,
            doc_type=[cls],
            model=cls._doc_type.model
        )

    def prepare_current_status(self, instance):
        if instance.states.current_state:
            return {
                'value': instance.states.current_state.value,
                'name': str(instance.states.current_state.name),
                'description': str(instance.states.current_state.description),
            }

    def prepare_image(self, instance):
        if instance.image:
            return {
                'id': instance.pk,
                'file': instance.image.file.name,
                'type': 'activity'
            }
        elif instance.initiative and instance.initiative.image:
            return {
                'id': instance.initiative.pk,
                'file': instance.initiative.image.file.name,
                'type': 'initiative'
            }

    def prepare_manager(self, instance):
        managers = [
            instance.owner.pk,
        ]
        if instance.initiative:
            managers.append(
                instance.initiative.owner.pk
            )

            for manager in instance.initiative.activity_managers.all():
                managers.append(manager.pk)
            if instance.initiative.promoter:
                managers.append(instance.initiative.promoter.pk)

        return managers

    def prepare_contributors(self, instance):
        return [
            contributor.user.pk for contributor
            in instance.contributors.filter(status__in=('succeeded', 'accepted'))
            if contributor.user
        ]

    def prepare_contributor_count(self, instance):
        return instance.contributors.filter(status__in=('succeeded', 'accepted')).count()

    def prepare_donation_count(self, instance):
        return instance.contributors.instance_of(Donor).filter(status='succeeded').count()

    def prepare_type(self, instance):
        return str(instance.__class__.__name__.lower())

    def prepare_resource_name(self, instance):
        return str(instance.__class__.JSONAPIMeta.resource_name)

    def prepare_activity_type(self, instance):
        mapping = {
            "dateactivity": "time",
            "deadlineactivity": "time",
            "periodicactivity": "time",
            "scheduleactivity": "time",
            "registereddateactivity": "time",
            "funding": "funding",
            "collectactivity": "collect",
            "deed": "deed",
            "grantapplication": "grantapplication",
        }
        return mapping[str(instance.__class__.__name__.lower())]

    def prepare_country(self, instance):
        countries = []
        if instance.office_location and instance.office_location.country:
            countries += get_translated_list(instance.office_location.country)
        if hasattr(instance, 'place') and instance.place and instance.place.country:
            countries += get_translated_list(instance.place.country)
        if instance.initiative and instance.initiative.place and instance.initiative.place.country:
            countries += get_translated_list(instance.initiative.place.country)
        return deduplicate(countries)

    def prepare_location(self, instance):
        locations = []
        if hasattr(instance, 'location') and instance.location:
            locations.append({
                'id': instance.location.id,
                'name': instance.location.formatted_address,
                'locality': instance.location.locality,
                'country_code': instance.location.country.alpha2_code,
                'country': instance.location.country.name,
                'type': 'location'
            })
        if hasattr(instance, 'office_location') and instance.office_location:
            locations.append({
                'id': instance.office_location.pk,
                'name': instance.office_location.name,
                'locality': instance.office_location.city,
                'country_code': (
                    instance.office_location.country.alpha2_code if
                    instance.office_location.country else None
                ),
                'country': (
                    instance.office_location.country.name if
                    instance.office_location.country else None
                ),
                'type': 'office'
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

    def prepare_office_restriction(self, instance):
        office = instance.office_location
        return {
            'restriction': instance.office_restriction,
            'office': office.id if office else None,
            'subregion': office.subregion.id if office and office.subregion_id else None,
            'region': office.subregion.region.id if office and office.subregion and office.subregion.region else None
        }

    def prepare_expertise(self, instance):
        if hasattr(instance, 'expertise') and instance.expertise:
            return get_translated_list(instance.expertise)

    def prepare_theme(self, instance):
        if instance.theme:
            return get_translated_list(instance.theme)

    def prepare_categories(self, instance):
        categories = []
        for category in instance.categories.all():
            categories += get_translated_list(category, 'title')

        return categories

    def prepare_segments(self, instance):

        segments = []
        for segment in instance.segments.all():
            segments += get_translated_segments(segment)
        return segments

    def prepare_is_online(self, instance):
        if hasattr(instance, 'is_online'):
            return instance.is_online

    def prepare_is_upcoming(self, instance):
        return instance.status in ['open', 'full']

    def prepare_position(self, instance):
        return []

    def prepare_end(self, instance):
        return None

    def prepare_start(self, instance):
        return None

    def prepare_created(self, instance):
        return instance.created

    def prepare_host_organization(self, instance):
        if not instance.host_organization:
            return None

        org = instance.host_organization
        logo_url = None
        if org.logo and org.logo.file:
            try:
                logo_url = tenant_url(org.logo.url)
            except (ValueError, AttributeError):
                logo_url = None

        return {
            'id': org.pk,
            'name': org.name,
            'logo': logo_url,
        }
