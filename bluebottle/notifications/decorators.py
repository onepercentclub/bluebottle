from django_fsm import transition as fsm_transition


def transition(*args, **kwargs):
    messages = kwargs.pop('messages', [])

    wrapped = fsm_transition(*args, **kwargs)

    def inner_transition(func):
        result = wrapped(func)

        setattr(result, 'messages', messages)

        return result

    return inner_transition
