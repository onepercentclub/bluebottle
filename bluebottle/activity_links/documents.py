from django.utils.timezone import now
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from bluebottle.activities.documents import ActivityDocument, activity
from bluebottle.activity_links.models import LinkedDeed


@registry.register_document
@activity.doc_type
class LinkedDeedDocument(ActivityDocument):

    link = fields.KeywordField()

    def get_queryset(self):
        return LinkedDeed.objects.all()

    def prepare_kind(self, instance):
        return "linked_activity"

    def get_doc_id(self, instance):
        return f"linked_{instance.pk}"

    def get_id(self, instance):
        return f"linked_{instance.pk}"

    def prepare_slug(self, instance):
        return f'linked-deed-{instance.id}'

    def prepare_type(self, instance):
        return 'deed'

    def prepare_resource_name(self, instance):
        return 'activities/deeds'

    def prepare_activity_type(self, instance):
        return 'deed'

    def prepare_current_status(self, instance):
        return {
            'value': 'open',
            'name': 'Open',
            'description': 'Open',
        }

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
        return []

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

    class Django:
        model = LinkedDeed
        related_models = ()  # No related models for LinkedDeed
