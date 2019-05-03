from django_fsm import transition as fsm_transition


def transition(*args, **kwargs):
    messages = kwargs.pop('messages', [])
    form = kwargs.pop('form', [])

    wrapped = fsm_transition(*args, **kwargs)

    def inner_transition(func):
        result = wrapped(func)

        setattr(result, 'messages', messages)
        setattr(result, 'form', form)

        return result

    return inner_transition
