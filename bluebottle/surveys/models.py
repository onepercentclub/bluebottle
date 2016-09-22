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
        for question in Question.objects.all():
            answers = itertools.groupby(
                Answer.objects.filter(question=question, value__isnull=False, response__project__isnull=False).order_by('response__project'),
                lambda answer: answer.response.project
            )
            answers_by_projects = {
                project: list(answers) for project, answers in answers
            }

            for project, values in answers_by_projects.items():
                aggregate_answer, _created = AggregateAnswer.objects.get_or_create(
                    project=project, question=question
                )
                aggregate_answer.update(values)

    def __unicode__(self):
        return self.title or self.remote_id


class Question(models.Model):

    AggregationChoices = (
        ('sum', 'Sum'),
        ('average', 'Average'),
        ('winner', 'Winner'),
    )

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)
    title =  models.CharField(max_length=500, blank=True, null=True)

    display = models.BooleanField(default=True)
    display_title =  models.CharField(max_length=500, blank=True, null=True)
    display_style = models.CharField(max_length=500, blank=True, null=True)

    aggregation = models.CharField(max_length=200, choices=AggregationChoices, null=True, blank=True)
    properties = JSONField(null=True)
    specification = JSONField(null=True)

    def clean(self):
        if not self.display_title:
            self.display_title = self.title

    def __unicode__(self):
        return self.title


class Response(models.Model):

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    submitted = models.DateTimeField(null=True, blank=True, auto_now=True)
    project = models.ForeignKey('projects.Project', null=True, blank=True)
    task = models.ForeignKey('tasks.Task', null=True, blank=True)
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

    response_count = models.IntegerField(null=True)

    value = models.FloatField(null=True)
    list = JSONField(null=True, default=[])
    options = JSONField(null=True, default={})

    def _aggregate_average(self, answers):
        self.value = sum(answer.float_value for answer in answers) / float(len(answers))

    def _aggregate_sum(self, answers):
        self.value = sum(answer.float_value for answer in answers)

    def aggregate_number(self, answers):
        if self.question.aggregation == 'sum':
            self._aggregate_sum(answers)
        else:
            self._aggregate_average(answers)

    def aggregate_multiplechoice(self, answers):
        values_by_options = itertools.groupby(
            sorted(answers, key=lambda answer: answer.value),
            lambda answer: answer.value
        )
        self.options = {
            value: len(list(answers)) for value, answers in values_by_options
        }

    def aggregate_list(self, answers):
        self.list = [answer.value for answer in answers]

    def update(self, answers):
        if self.question.type in ('number', 'slider'):
            self.aggregate_number(answers)
        elif self.question.type == 'radio':
            self.aggregate_multiplechoice(answers)
        else:
            self.aggregate_list(answers)

        self.response_count = len(answers)
        self.save()
