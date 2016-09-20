import urllib
import itertools

from django.db import models
from django_extensions.db.fields.json import JSONField
from django_extensions.db.fields import (ModificationDateTimeField,
                                         CreationDateTimeField)


class Survey(models.Model):
    remote_id = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True, default={})
    link = models.URLField(null=True)
    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    def url(self, task):
        query_params = {
            'theme': task.project.theme.slug,
            'task_id': task.id,
            'project_id': task.project.id
        }

        return '{}?{}'.format(self.link, urllib.urlencode(query_params))

    def aggregate(self):
        for question in Question.objects.exclude(aggregation__isnull=True, survey=self):
            answers = itertools.groupby(
                Answer.objects.filter(question=question, response__project__isnull=False).order_by('response__project'),
                lambda answer: answer.response.project
            )
            answers_by_projects = {
                project: [answer.float_value for answer in answers] for project, answers in answers
            }

            for project, values in answers_by_projects.items():
                if question.aggregation == 'sum':
                    value = sum(value for value in values)
                else:
                    value = sum(value for value in values) / float(len(values))

                AggregateAnswer.objects.get_or_create(
                    project=project,
                    question=question,
                    defaults={'value': value}
                )

    def __unicode__(self):
        return self.title or self.remote_id


class Question(models.Model):

    AggregationChoices = (
        ('sum', 'Sum'),
        ('average', 'Average'),
    )

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)
    title =  models.CharField(max_length=500, blank=True, null=True)

    aggregation = models.CharField(max_length=200, choices=AggregationChoices, null=True, blank=True)
    properties = JSONField(null=True)
    specification = JSONField(null=True)

    def __unicode__(self):
        return self.title


class Response(models.Model):

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    submitted = models.DateTimeField(null=True)
    project = models.ForeignKey('projects.Project', null=True)
    task = models.ForeignKey('tasks.Task', null=True)
    specification = JSONField(null=True)


class Answer(models.Model):

    response = models.ForeignKey('surveys.Response')
    question = models.ForeignKey('surveys.Question')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
    value = models.CharField(max_length=5000, blank=True)

    @property
    def float_value(self):
        try:
            return float(self.value)
        except ValueError:
            return 0


class AggregateAnswer(models.Model):
    question = models.ForeignKey('surveys.Question')
    project = models.ForeignKey('projects.Project')

    value = models.FloatField()


