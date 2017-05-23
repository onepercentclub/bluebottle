from django.db.models.signals import post_save
from django.dispatch import receiver

from .utils import process


@receiver(post_save, weak=False, dispatch_uid='model_analytics')
def post_save_analytics(sender, instance, **kwargs):
    process(instance, kwargs['created'])
