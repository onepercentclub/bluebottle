from functools import wraps

from django.utils.module_loading import import_string

from django_fsm import FSMMeta, Transition


class NotificationTransition(Transition):
    def __init__(self, method, source, target, on_error, conditions, permission, custom, messages, form):
        super(NotificationTransition, self).__init__(
            method, source, target, on_error, conditions, permission, custom
        )
        self.messages = messages
        self.form = form


class FSMNotificationsMeta(FSMMeta):
    def add_transition(
        self, method, source, target, on_error=None, conditions=[],
        permission=None, custom={}, messages=[], form=None
    ):
        if source in self.transitions:
            raise AssertionError('Duplicate transition for {0} state'.format(source))

        self.transitions[source] = NotificationTransition(
            method=method,
            source=source,
            target=target,
            on_error=on_error,
            conditions=conditions,
            permission=permission,
            form=form,
            messages=messages,
            custom=custom)


def transition(
    field, source='*', target=None, on_error=None, conditions=[],
    permission=None, custom={}, messages=[], form=None
):
    """
    Method decorator for mark allowed transitions

    Set target to None if current state needs to be validated and
    has not changed after the function call
    """
    def inner_transition(func):
        wrapper_installed, fsm_meta = True, getattr(func, '_django_fsm', None)
        if not fsm_meta:
            wrapper_installed = False
            fsm_meta = FSMNotificationsMeta(field=field, method=func)
            setattr(func, '_django_fsm', fsm_meta)

        form_class = import_string(form) if form else None

        if isinstance(source, (list, tuple, set)):
            for state in source:
                func._django_fsm.add_transition(
                    func, state, target, on_error, conditions, permission, custom, messages, form_class
                )
        else:
            func._django_fsm.add_transition(
                func, source, target, on_error, conditions, permission, custom, messages, form_class
            )

        @wraps(func)
        def _change_state(instance, *args, **kwargs):
            transition = fsm_meta.get_transition(getattr(instance, field))
            return fsm_meta.field.change_state(instance, func, transition=transition, *args, **kwargs)

        if not wrapper_installed:
            _change_state.messages = messages
            return _change_state

        return func

    return inner_transition
