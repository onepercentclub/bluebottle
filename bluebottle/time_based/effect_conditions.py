"""Light-weight effect predicates for periodic tasks.

Kept import-free so ``periodic_tasks`` can use them without pulling in
``time_based.triggers`` (whose package ``__init__`` imports activities that
depend on ``activities.triggers``, which is not finished loading during model
import).
"""


def has_participants(effect):
    return len(effect.instance.active_participants) > 0


def has_no_participants(effect):
    return len(effect.instance.active_participants) == 0
