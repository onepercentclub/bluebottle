from functools import wraps

from django_fsm import FSMMeta


def transition(field, source='*', target=None, on_error=None, conditions=[], permission=None, messages=None, custom={}):
    # EDIT
    if not messages:
        messages = []
    # end

    def inner_transition(func):
        wrapper_installed, fsm_meta = True, getattr(func, '_django_fsm', None)
        if not fsm_meta:
            wrapper_installed = False
            fsm_meta = FSMMeta(field=field, method=func)
            setattr(func, '_django_fsm', fsm_meta)
        setattr(func, 'messages', messages)

        if isinstance(source, (list, tuple, set)):
            for state in source:
                func._django_fsm.add_transition(func, state, target, on_error, conditions, permission, custom)
        else:
            func._django_fsm.add_transition(func, source, target, on_error, conditions, permission, custom)

        @wraps(func)
        def _change_state(instance, *args, **kwargs):
            return fsm_meta.field.change_state(instance, func, *args, **kwargs)

        if not wrapper_installed:
            return _change_state

        return func

    return inner_transition
