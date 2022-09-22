from builtins import str
from django_elasticsearch_dsl import Document, fields

from bluebottle.funding.models import Donor
from bluebottle.utils.documents import MultiTenantIndex
from bluebottle.activities.models import Activity
from bluebottle.utils.search import Search
from elasticsearch_dsl.field import DateRange
from bluebottle.members.models import Member

from bluebottle.initiatives.models import Initiative, Theme


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
    highlight = fields.BooleanField()

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
        'owner': fields.KeywordField(attr='owner.id'),
        'activity_managers': fields.NestedField(
            properties={
                'id': fields.KeywordField(),
            }
        )
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
            'language': fields.KeywordField(),
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

    contributors = fields.DateField()
    contributor_count = fields.IntegerField()
    donation_count = fields.IntegerField()

    start = fields.DateField()
    end = fields.DateField()

    duration = DateRangeField()
    activity_date = fields.DateField()

    def get_instances_from_related(self, related_instance):
        model = self.Django.model

        if isinstance(related_instance, Initiative):
            return model.objects.filter(initiative=related_instance)
        if isinstance(related_instance, Theme):
            return model.objects.filter(initiative__theme=related_instance)
        if isinstance(related_instance, Theme.translations.field.model):
            return model.objects.filter(initiative__theme=related_instance.master)
        if isinstance(related_instance, Member):
            return model.objects.filter(owner=related_instance)

    class Django:
        related_models = (Initiative, Theme, Theme.translations.field.model, Member)
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

    def prepare_location(self, instance):
        locations = []
        if hasattr(instance, 'location') and instance.location:
            locations.append({
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
        elif instance.initiative.location:

            locations.append({
                'id': instance.initiative.location.pk,
                'name': instance.initiative.location.name,
                'locality': instance.initiative.location.city,
                'country_code': (
                    instance.initiative.location.country.alpha2_code if
                    instance.initiative.location.country else None
                ),
                'country': (
                    instance.initiative.location.country.name if
                    instance.initiative.location.country else None
                ),
                'type': 'initiative_office'
            })
        elif instance.initiative.place:
            locations.append({
                'locality': instance.initiative.place.locality,
                'country_code': instance.initiative.place.country.alpha2_code,
                'country': instance.initiative.place.country.name,
                'type': 'impact_location'
            })
        return locations

    def prepare_expertise(self, instance):
        if hasattr(instance, 'expertise') and instance.expertise:
            return [
                {
                    'id': instance.expertise_id,
                    'name': translation.name,
                    'language': translation.language_code,
                }
                for translation in instance.expertise.translations.all()
            ]

    def prepare_theme(self, instance):
        if hasattr(instance.initiative, 'theme') and instance.initiative.theme:
            return [
                {
                    'id': instance.initiative.theme_id,
                    'name': translation.name,
                    'language': translation.language_code,
                }
                for translation in instance.initiative.theme.translations.all()
            ]

    def prepare_is_online(self, instance):
        if hasattr(instance, 'is_online'):
            return instance.is_online

    def prepare_position(self, instance):
        return None

    def prepare_end(self, instance):
        return None

    def prepare_start(self, instance):
        return None
