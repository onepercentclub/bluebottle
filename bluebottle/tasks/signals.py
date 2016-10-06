from bluebottle.tasks.models import Task, TaskMember
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


@receiver(pre_save, weak=False, sender=TaskMember,
          dispatch_uid='set-hours-spent-taskmember')
def set_hours_spent_taskmember(sender, instance, **kwargs):
    if instance.status != instance._initial_status and instance.status == TaskMember.TaskMemberStatuses.realized:
        instance.time_spent = instance.task.time_needed


# post save members needed
@receiver(post_save, sender=TaskMember,
          dispatch_uid="bluebottle.tasks.TaskMember.post_save")
def calculate_members_needed(sender, instance, **kwargs):
    task = instance.task
    members = TaskMember.objects.filter(
        task=task,
        status__in=('accepted', 'realized')
    )
    total_externals = 0
    for member in members:
        total_externals += member.externals

    people_accepted = members.count() + total_externals

    if task.status == Task.TaskStatuses.open and task.people_needed <= people_accepted:
        task.set_in_progress()

    if task.status == Task.TaskStatuses.in_progress and task.people_needed > people_accepted:
        task.set_open()
    task.save()
