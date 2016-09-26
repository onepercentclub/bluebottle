import urllib
import itertools
from collections import Counter

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

    def synchronize(self):
        from bluebottle.surveys.adapters import SurveyGizmoAdapter

        survey_adapter = SurveyGizmoAdapter()
        survey_adapter.update_survey(self)

    def aggregate(self):
        for question in Question.objects.all():

            # Calculate aggregates by task
            task_answers = itertools.groupby(
                Answer.objects.filter(question=question, value__isnull=False,
                                      response__task__isnull=False).order_by('response__project'),
                lambda answer: answer.response.project
            )
            answers_by_tasks = {
                task: list(answers) for task, answers in task_answers
            }

            for task, values in answers_by_tasks.items():
                aggregate_task_answer, _created = AggregateAnswer.objects.get_or_create(
                    task=task, project=task.project, aggregation_type='task', question=question
                )
                aggregate_answer.update(values)

            # Calculate aggregates by project
            project_answers = itertools.groupby(
                Answer.objects.filter(question=question, value__isnull=False,
                                      response__task__isnull=True,
                                      response__project__isnull=False).order_by('response__project'),
                lambda answer: answer.response.project
            )

            answers_by_projects = {
                project: list(answers) for project, answers in project_answers
            }

            for project, values in answers_by_projects.items():
                aggregate_answer, _created = AggregateAnswer.objects.get_or_create(
                    project=project, question=question,
                    aggregation_type='task'
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
    title = models.CharField(max_length=500, blank=True, null=True)

    display = models.BooleanField(default=True)
    display_title = models.CharField(max_length=500, blank=True, null=True)
    display_style = models.CharField(max_length=500, blank=True, null=True)

    aggregation = models.CharField(max_length=200, choices=AggregationChoices, null=True, blank=True)
    properties = JSONField(null=True)
    specification = JSONField(null=True)

    def save(self, *args, **kwargs):
        if not self.display_title:
            self.display_title = self.title
        return super(Question, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title


class SubQuestion(models.Model):

    remote_id = models.CharField(max_length=200, blank=True, null=True)
    question = models.ForeignKey('surveys.Question')
    type = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    specification = JSONField(null=True)

    def __unicode__(self):
        return self.title


class Response(models.Model):

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    submitted = models.DateTimeField(null=True, blank=True)
    project = models.ForeignKey('projects.Project', null=True, blank=True)
    task = models.ForeignKey('tasks.Task', null=True, blank=True)
    specification = JSONField(null=True)
    params = JSONField(null=True)


class Answer(models.Model):

    response = models.ForeignKey('surveys.Response')
    question = models.ForeignKey('surveys.Question')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
    value = models.CharField(max_length=5000, blank=True)
    options = JSONField(null=True)

    @property
    def float_value(self):
        try:
            return float(self.value.replace('%', ''))
        except ValueError:
            return 0


class AggregateAnswer(models.Model):

    AGGREGATION_TYPES = (
        ('project', 'project'),
        ('task', 'Task'),
        ('tasks', 'Tasks on project level'),
        ('all', 'Project and tasks')
    )

    question = models.ForeignKey('surveys.Question')
    project = models.ForeignKey('projects.Project', null=True)
    task = models.ForeignKey('tasks.Task', null=True)

    aggregation_type = models.CharField(max_length=20,
                                        choices=AGGREGATION_TYPES,
                                        default='project')
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

    def aggregate_multiple_choice(self, answers):
        """
        Count how many times an item is picked (radio or checkbox)
        {'Cheese': 4, 'Peperoni': 3, 'Pineapple': 0}
        """
        results = [a.options for a in answers]
        if len(results):
            options = Counter()
            for item in results:
                options.update(item)
            self.options = {k: v for k, v in options.items()}

    def aggregate_table_radio(self, answers):
        """
        Get the scores for all items in a radio-table and average them.
        {{'Before': 5.6,
        """
        results = [a.options for a in answers]
        if len(results):
            options = Counter()
            for item in results:
                options.update(item)
            self.options = {k: float(v) / len(results) for k, v in options.items()}

    def aggregate_list(self, answers):
        self.list = [answer.value for answer in answers]

    def update(self, answers):
        if self.question.type in ('number', 'slider', 'percent'):
            self.aggregate_number(answers)
        elif self.question.type in ('radio', 'checkbox'):
            self.aggregate_multiple_choice(answers)
        elif self.question.type == 'table-radio':
            self.aggregate_table_radio(answers)
        else:
            self.aggregate_list(answers)

        self.response_count = len(answers)
        self.save()
