import uuid
from datetime import date, timedelta
from django.db import models
from djchoices import DjangoChoices, ChoiceItem
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext
from django_extensions.db.fields import (
    ModificationDateTimeField, CreationDateTimeField)
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.projects.models import Project


class Suggestion(models.Model):
    class Statuses(DjangoChoices):
        unconfirmed = ChoiceItem('unconfirmed', label=_('Unconfirmed email'))
        draft = ChoiceItem('draft', label=_('Draft'))
        accepted = ChoiceItem('accepted', label=_('Accepted'))
        rejected = ChoiceItem('rejected', label=_('Rejected'))
        # To prevent the translationsin booking for overwriting this
        # translation we use pgettext
        in_progress = ChoiceItem('in_progress',
                                 label=pgettext('suggestion label',
                                                'In progress'))
        submitted = ChoiceItem('submitted', label=_('Submitted'))

    created = CreationDateTimeField(_('created'), help_text=_(
        'When this project was created.'))
    updated = ModificationDateTimeField(_('updated'), help_text=_(
        'When this project was updated.'))

    title = models.TextField()  # description
    pitch = models.TextField()  # requirements
    deadline = models.DateField()  # date
    theme = models.ForeignKey(ProjectTheme)
    destination = models.CharField(max_length=100)

    org_name = models.CharField(max_length=100)
    org_contactname = models.CharField(max_length=100)
    org_email = models.EmailField()
    org_phone = models.CharField(max_length=64)
    org_website = models.URLField()

    status = models.CharField(_("status"), choices=Statuses.choices,
                              max_length=64,
                              default="unconfirmed")
    token = models.CharField(max_length=100, blank=True, null=True)

    project = models.ForeignKey(Project, related_name="suggestions",
                                null=True, blank=True)
    language = models.CharField(_('suggestion language'), max_length=10, default='en')

    def confirm(self):
        if self.status == "unconfirmed":
            self.status = 'draft'
            self.save()
            return True

        return False

    @property
    def expired(self):
        # Expired will return False if the deadline is today
        return self.deadline - date.today() < timedelta(0)

    def __unicode__(self):
        return u'Suggestion "{0}" from {1}'.format(self.title,
                                                   self.org_contactname)

    def save(self, *args, **kwargs):
        if not self.pk and not self.token:
            token = str(uuid.uuid4())
            self.token = token
        super(Suggestion, self).save(*args, **kwargs)

import signals  # noqa
