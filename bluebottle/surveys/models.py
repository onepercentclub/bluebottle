from django.db import models
from django_extensions.db.fields.json import JSONField


class Survey(models.Model):

    remote_id = models.CharField(max_length=200, blank=True, null=True)


class Question(models.Model):

    survey = models.ForeignKey('surveys.Survey')
    remote_id = models.CharField(max_length=200, blank=True, null=True)
    specification = JSONField(null=True)
