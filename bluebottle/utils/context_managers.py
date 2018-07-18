from contextlib import contextmanager


@contextmanager
def LogMail(logs, type):
    already_send = logs.filter(type=type).exists()
    yield already_send

    if not already_send:
        logs.create(type=type)


