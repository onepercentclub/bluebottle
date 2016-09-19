import urllib
from django.db import models
from django_extensions.db.fields.json import JSONField


class Survey(models.Model):
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
    link = models.URLField()

    def url(self, task):
        query_params = {
            'theme': task.project.theme.slug,
            'task_id': task.id,
            'project_id': task.project.id
        }

        return '{}?{}'.format(self.link, urllib.urlencode(query_params))


class Question(models.Model):

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
