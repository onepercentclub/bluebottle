from bluebottle.bb_tasks.models import (BaseSkill, BaseTask, BaseTaskFile,
                                        BaseTaskMember)

GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_task', 'change_task', 'delete_task',
            'add_taskmember', 'change_taskmember', 'delete_taskmember',
        )
    }
}

class Task(BaseTask):
    pass


class Skill(BaseSkill):
    pass


class TaskMember(BaseTaskMember):
    pass


class TaskFile(BaseTaskFile):
    pass
