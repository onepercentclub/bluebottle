from django.db import models


class Translation(models.Model):
    text = models.TextField()
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    translation = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True)
