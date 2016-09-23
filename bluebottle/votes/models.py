from django.db import models
from django.conf import settings

from django.utils.translation import ugettext as _
from django_extensions.db.fields import CreationDateTimeField


class Vote(models.Model):
    """
    Mixin for generating an invoice reference.
    """
    created = CreationDateTimeField(_('created'))
    project = models.ForeignKey('projects.Project')
    ip_address = models.GenericIPAddressField()

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('voter'))

    def __unicode__(self):
        return "{0} -> {1}".format(self.voter, self.project)

    class Analytics:
        type = 'vote'
        tags = {}
        fields = {
            'id': 'id',
            'user_id': 'voter.id',
            'project_id': 'project.id'
        }

    class Meta:
        unique_together = (('project', 'voter'),)
        ordering = ('-created',)

    @classmethod
    def has_voted(cls, voter, project):
        """ Check if a user has voted for a project.

        Users are allowed to vote on a project only once.
        User are allowed to vote once on active project within a category
        """
        if voter.is_anonymous():
            return False

        if len(Vote.objects.filter(project=project, voter=voter)) > 0:
            return True

        for category in project.categories.all():
            # Make sure our vote is unique among the active projects in this category
            if len(cls.objects.filter(
                project__categories=category,
                project__status__slug='voting',
                voter=voter
            )):
                return True

        return False
