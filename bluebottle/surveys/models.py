import urllib
import itertools
from collections import Counter, defaultdict

import bleach

from django.db import models
from django.utils.translation import ugettext_lazy as _

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
    last_synced = models.DateTimeField(null=True)
    active = models.BooleanField(default=False, help_text=_('Should this survey be used in emails?'))

    @property
    def questions(self):
        return self.question_set.order_by('id')

    @property
    def visible_questions(self):
        return self.question_set.filter(display=True).order_by('id')

    @classmethod
    def url(cls, project_or_task, user_type='task_member'):
        try:
            survey = cls.objects.filter(active=True).order_by('-created').all()[0]
        except IndexError:
            return None

        if hasattr(project_or_task, 'project'):
            project = project_or_task.project
            task = project_or_task
        else:
            project = project_or_task
            task = None

        if not project.celebrate_results:
            return None

        query_params = {
            'theme': project.theme.slug,
            'project_id': project.id,
            'user_type': user_type
        }

        if task:
            query_params['task_id'] = task.id

        return '{}?{}'.format(survey.link, urllib.urlencode(query_params))

    def synchronize(self):
        from bluebottle.surveys.adapters import SurveyGizmoAdapter

        survey_adapter = SurveyGizmoAdapter()
        survey_adapter.update_survey(self)

    def _aggregate_projects(self):
        for question in self.question_set.all():

            # Calculate aggregates by project
            project_answers = itertools.groupby(
                Answer.objects.filter(question=question,
                                      value__isnull=False,
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
                    aggregation_type='project'
                )
                aggregate_answer.update(values)

    def _aggregate_tasks(self):
        # Calculate aggregates by task
        for question in self.question_set.all():
            task_answers = itertools.groupby(
                Answer.objects.filter(question=question,
                                      value__isnull=False,
                                      response__task__isnull=False).order_by('response__task'),
                lambda answer: answer.response.task
            )
            answers_by_tasks = {
                task: list(answers) for task, answers in task_answers
            }

            for task, values in answers_by_tasks.items():
                aggregate_answer, _created = AggregateAnswer.objects.get_or_create(
                    task=task, project=task.project,
                    aggregation_type='task', question=question
                )
                aggregate_answer.update(values)

    def _aggregate_tasks_by_project(self):
        # Calculate aggregates of all tasks in a project
        for question in self.question_set.all():
            task_aggregates = itertools.groupby(
                AggregateAnswer.objects.filter(question=question,
                                               aggregation_type='task').order_by('project'),
                lambda answer: answer.project
            )
            answers_by_project = {
                project: list(answers) for project, answers in task_aggregates
            }
            for project, values in answers_by_project.items():
                if len(values):
                    aggregate_answer, _created = AggregateAnswer.objects.get_or_create(
                        project=project,
                        aggregation_type='project_tasks', question=question
                    )
                    aggregate_answer.update(values)

    def _aggregate_project_initiators(self):
        for question in self.question_set.all():

            # Calculate aggregates by project
            project_answers = itertools.groupby(
                Answer.objects.filter(question=question,
                                      value__isnull=False,
                                      response__user_type='initiator',
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
                    aggregation_type='initiator'
                )
                aggregate_answer.update(values)

    def _aggregate_project_organizations(self):
        for question in self.question_set.all():

            # Calculate aggregates by project
            project_answers = itertools.groupby(
                Answer.objects.filter(question=question,
                                      value__isnull=False,
                                      response__user_type='organization',
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
                    aggregation_type='organization'
                )
                aggregate_answer.update(values)

    def _aggregate_combined(self):
        # Combine project tasks with initators and organizations
        for question in self.question_set.all():
            combined_aggregates = itertools.groupby(
                AggregateAnswer.objects.filter(aggregation_type__in=['project_tasks',
                                                                     'initiator',
                                                                     'organization'],
                                               question=question,).order_by('project'),
                lambda answer: answer.project
            )
            answers_by_project = {
                project: list(answers) for project, answers in combined_aggregates
            }

            for project, values in answers_by_project.items():
                aggregate_answer, _created = AggregateAnswer.objects.get_or_create(
                    project=project,
                    question=question,
                    aggregation_type='combined'
                )
                aggregate_answer.update(values)

    def aggregate(self):
        self._aggregate_tasks()
        self._aggregate_projects()
        self._aggregate_tasks_by_project()
        self._aggregate_project_initiators()
        self._aggregate_project_organizations()
        self._aggregate_combined()

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
    display_theme = models.CharField(max_length=50, blank=True, null=True)
    display_title = models.CharField(max_length=500, blank=True, null=True)
    display_style = models.CharField(max_length=500, blank=True, null=True)
    left_label = models.CharField(max_length=200, blank=True, null=True)
    right_label = models.CharField(max_length=200, blank=True, null=True)

    aggregation = models.CharField(max_length=200, choices=AggregationChoices, null=True, blank=True)
    properties = JSONField(null=True)
    specification = JSONField(null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.display_title = self.title
            try:
                self.left_label = self.properties['left_label']
            except KeyError:
                pass
            try:
                self.right_label = self.properties['right_label']
            except KeyError:
                pass
        return super(Question, self).save(*args, **kwargs)

    def get_platform_aggregate(self, start=None, end=None):
        answers = self.aggregateanswer_set.filter(aggregation_type='combined').all()

        if start:
            answers = answers.filter(project__campaign_ended__gte=start)
        if end:
            answers = answers.filter(project__campaign_ended__lte=end)

        if self.type in ('number', 'slider', 'percent'):
            if (self.aggregation == 'average'):
                return answers.aggregate(value=models.Avg('value'))['value']
            else:
                return answers.aggregate(value=models.Sum('value'))['value']
        elif self.type in ('radio', 'checkbox', 'table-radio'):
            values = defaultdict(list)
            for answer in answers:
                [values[key].append(value) for key, value in answer.options.items()]
            return dict((key, float(sum(value)) / len(value)) for key, value in values.items())

    def __unicode__(self):
        return bleach.clean(unicode(self.title), strip=True, tags=[])


class SubQuestion(models.Model):

    remote_id = models.CharField(max_length=200, blank=True, null=True)
    question = models.ForeignKey('surveys.Question')
    type = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    display_title = models.CharField(max_length=500, blank=True, null=True)
    specification = JSONField(null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.display_title = self.title
        return super(SubQuestion, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title


class Response(models.Model):

    USER_TYPES = (
        ('task_member', _('Task member')),
        ('initiator', _('Project initiator')),
        ('organization', _('Partner organisation'))
    )

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    submitted = models.DateTimeField(null=True, blank=True)
    project = models.ForeignKey('projects.Project', null=True, blank=True)
    task = models.ForeignKey('tasks.Task', null=True, blank=True)
    user_type = models.CharField(max_length=200, choices=USER_TYPES,
                                 blank=True, null=True)
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
        ('project', _('Project')),
        ('initiator', _('Project initiator')),
        ('organization', _('Partner organisation')),
        ('task', _('Task')),
        ('project_tasks', _('Tasks in project')),
        ('combined', _('Project and tasks'))
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

    @property
    def float_value(self):
        return self.value

    def _aggregate_average(self, answers):
        self.value = sum(answer.float_value for answer in answers) / float(len(answers))

    def _aggregate_sum(self, answers):
        self.value = sum(answer.float_value for answer in answers)

    def aggregate_number(self, answers):
        # See if we want to sum the values here.
        if self.aggregation_type == 'project_tasks' and self.question.aggregation == 'sum':
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
        {{'Before': 5.6, 'After': 8.7}}
        """
        results = [a.options for a in answers]
        if len(results):
            options = Counter()
            item_length = 0
            for item in results:
                if bool(item):
                    item_length += 1
                    options.update(item)
            result = {k: float(v) / item_length for k, v in options.items()}
            self.options = {}
            for sub in self.question.subquestion_set.all():
                try:
                    self.options[sub.title] = result[sub.title]
                except KeyError:
                    pass

    def aggregate_list(self, answers):
        if isinstance(answers[0], AggregateAnswer):
            self.list = []
            for answer in answers:
                self.list += answer.list
                self.list = sorted(self.list)
        else:
            self.list = sorted([answer.value for answer in answers])

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
