import urllib
from django.db import models
from django_extensions.db.fields.json import JSONField
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)


class Survey(models.Model):
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
    link = models.URLField()

    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    def url(self, task):
        query_params = {
            'theme': task.project.theme.slug,
            'task_id': task.id,
            'project_id': task.project.id
        }

        return '{}?{}'.format(self.link, urllib.urlencode(query_params))

    def __unicode__(self):
        return self.title


class Question(models.Model):

    AggregationChoices = (
        ('sum', 'Sum'),
        ('average', 'Average'),
    )

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)
    title =  models.TextField(blank=True, null=True)

    aggregation = models.CharField(max_length=200, choices=AggregationChoices, null=True)
    properties = JSONField(null=True)
    specification = JSONField(null=True)


class Response(models.Model):

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)


class Answer(models.Model):

    response = models.ForeignKey('surveys.Response')
    question = models.ForeignKey('surveys.Question')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
