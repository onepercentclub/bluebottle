from django.utils.timezone import now
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedActivity


class LinkedActivityDocument(ActivityDocument):
    class Django:
        related_models = []
        model = LinkedActivity

    link = fields.KeywordField()

    def get_queryset(self):
        return self.django.model._default_manager.all()

    def prepare_kind(self, instance):
        return "linked_activity"

    def get_doc_id(self, instance):
        return f"linked_{instance.pk}"

    def get_id(self, instance):
        return f"linked_{instance.pk}"

    def prepare_current_status(self, instance):
        return {
            'value': 'open',
            'name': 'Open',
            'description': 'Open',
        }

    def prepare_link(self, instance):
        return instance.link

    def prepare_is_online(self, instance):
        return True

    def prepare_is_upcoming(self, instance):
        return instance.status in ['open', 'running', 'full']

    def prepare_highlight(self, instance):
        return False

    def prepare_team_activity(self, instance):
        return 'individuals'

    def prepare_dates(self, instance):
        from datetime import datetime
        now = datetime.now()
        return [{
            'start': now,
            'end': now,
        }]

    # Override methods that don't apply to LinkedDeed
    def prepare_manager(self, instance):
        return []

    def prepare_contributors(self, instance):
        return []

    def prepare_contributor_count(self, instance):
        return 0

    def prepare_donation_count(self, instance):
        return 0

    def prepare_capacity(self, instance):
        return None

    def prepare_position(self, instance):
        return []

    def prepare_start(self, instance):
        return []

    def prepare_end(self, instance):
        return []

    def prepare_activity_date(self, instance):
        return []

    def prepare_image(self, instance):
        if instance.image:
            return {
                'id': instance.pk,
                'file': instance.image.file.name,
                'type': 'activity'
            }
        return {}

    def prepare_owner(self, instance):
        return []

    def prepare_initiative(self, instance):
        return []

    def prepare_categories(self, instance):
        return []

    def prepare_country(self, instance):
        return []

    def prepare_expertise(self, instance):
        return []

    def prepare_segments(self, instance):
        return []

    def prepare_location(self, instance):
        return []

    def prepare_office(self, instance):
        return []

    def prepare_office_subregion(self, instance):
        return []

    def prepare_office_region(self, instance):
        return []

    def prepare_office_restriction(self, instance):
        return []

    def prepare_theme(self, instance):
        return []

    def prepare_slots(self, instance):
        return []

    def prepare_created(self, instance):
        return now()


@registry.register_document
@activity.doc_type
class LinkedDeedDocument(LinkedActivityDocument):
    class Django:
        model = LinkedDeed
        related_models = ()

    def prepare_slug(self, instance):
        return f'linked-deed-{instance.id}'

    def prepare_type(self, instance):
        return 'deed'

    def prepare_resource_name(self, instance):
        __import__('ipdb').set_trace()
        return 'activities/deeds'

    def prepare_activity_type(self, instance):
        return 'deed'


@registry.register_document
@activity.doc_type
class LinkedFundingDocument(LinkedActivityDocument):
    class Django:
        model = LinkedFunding
        related_models = ()

    target = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })
    amount_raised = fields.NestedField(properties={
        'currency': fields.KeywordField(),
        'amount': fields.FloatField(),
    })

    def prepare_slug(self, instance):
        return f'linked-funding-{instance.id}'

    def prepare_type(self, instance):
        return 'funding'

    def prepare_resource_name(self, instance):
        return 'activities/fundings'

    def prepare_activity_type(self, instance):
        return 'funding'

    def prepare_amount(self, amount):
        if amount:
            return {'amount': amount.amount, 'currency': str(amount.currency)}

    def prepare_target(self, instance):
        if not hasattr(instance, 'target'):
            return None
        return self.prepare_amount(instance.target)

    def prepare_amount_raised(self, instance):
        if not hasattr(instance, 'donated'):
            return None
        return self.prepare_amount(instance.donated)
