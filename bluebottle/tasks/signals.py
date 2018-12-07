from bluebottle.tasks.models import Task, TaskMember, TaskStatusLog, TaskMemberStatusLog
from django.db.models.signals import post_init, post_save, pre_save
from django.dispatch import receiver


# post_init to store state on model
@receiver(post_init, sender=Task,
          dispatch_uid="bluebottle.tasks.Task.post_init")
def task_post_init(sender, instance, **kwargs):
    instance._init_status = instance.status


# post save to check if changed?
@receiver(post_save, sender=Task,
          dispatch_uid="bluebottle.tasks.Task.post_save")
def task_post_save(sender, instance, **kwargs):
    try:
        if instance._init_status != instance.status:
            instance.status_changed(instance._init_status, instance.status)
    except AttributeError:
        pass

    instance._init_status = instance.status


@receiver(pre_save, weak=False, sender=TaskMember,
          dispatch_uid='set-hours-spent-taskmember')
def set_hours_spent_taskmember(sender, instance, **kwargs):
    if instance.status != instance._initial_status \
            and instance.status == TaskMember.TaskMemberStatuses.realized \
            and not instance.time_spent:
        instance.time_spent = instance.task.time_needed


# post save members needed
@receiver(post_save, sender=TaskMember,
          dispatch_uid="bluebottle.tasks.TaskMember.post_save")
def check_accepted_members_status(sender, instance, **kwargs):
    instance.task.members_changed()


@receiver(post_save, sender=Task)
def create_task_status_log(sender, instance, created, **kwargs):
    # Only log task status if the status has changed
    if instance._original_status != instance.status or created:
        TaskStatusLog.objects.create(
            task=instance, status=instance.status)


@receiver(post_save, sender=TaskMember)
def create_task_member_status_log(sender, instance, created, **kwargs):
    # Only log task status if the status has changed
    if instance._original_status != instance.status or created:
        TaskMemberStatusLog.objects.create(
            task_member=instance, status=instance.status)
