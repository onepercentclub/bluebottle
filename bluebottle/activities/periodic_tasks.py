from datetime import timedelta

from django.utils import timezone 
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.messages import PublishActivityReminderNotification
from bluebottle.activities.models import Activity
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect

class UnpublishedActivitiesReminderTask(ModelPeriodicTask):
    def get_queryset(self):
        return Activity.objects.filter(
            polymorphic_ctype__model__in=('dateactivity', 'deed'),
            polymorphic_ctype__app_label__in=('time_based', 'deeds'),
            created__lte=timezone.now() - timedelta(days=3),
            created__gte=timezone.now() - timedelta(days=4),
            status__in=['draft', 'needs_work']
        )

    effects = [
        NotificationEffect(
            PublishActivityReminderNotification
        ),
    ]

    def __str__(self):
        return str(
            _("Send a reminder whe activities are unpublished for more then 3 days")
        )
