from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tools.middlewares.ThreadLocal import get_current_user

from bluebottle.deeds.models import Deed
from bluebottle.initiatives.models import Initiative

PLATFORM_CHOICES = (
    ('nlcares', 'NLCares'),
    ('onepercent', '1%Club'),
    ('voor_je_buurt', 'Voor je buurt'),
)


class PlatformConnection(models.Model):
    platform = models.CharField(
        max_length=100,
        help_text=_('Name of platform you want to receive activities from. For now use schema_name'),
        choices=PLATFORM_CHOICES
    )


class SharedActivity(models.Model):
    title = models.CharField(
        max_length=100
    )

    data = models.JSONField(
    )

    platform = models.CharField(
        max_length=100,
        choices=PLATFORM_CHOICES
    )

    remote_id = models.CharField(
        max_length=100,
    )

    activity = models.ForeignKey('activities.Activity', null=True, on_delete=models.SET_NULL)

    created = models.DateTimeField(auto_now_add=True)

    def accept(self):
        user = get_current_user()
        initiative, _created = Initiative.objects.get_or_create(
            title=f'Activities from {self.platform}',
            owner=user,
            status='approved'
        )

        deed = Deed.objects.create(
            title=self.data['title'],
            remote_id=self.remote_id,
            source_platform=self.platform,
            description=self.data['description'],
            owner=user,
            initiative=initiative
        )
        self.activity = deed
        self.save()
