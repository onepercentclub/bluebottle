from contextlib import ContextDecorator
from django.utils import translation


class override(ContextDecorator):
    def __init__(self, language):
        self.language = language or 'en'

    def __enter__(self):
        self.old_language = translation.get_language() or 'en'
        translation.activate(self.language)

    def __exit__(self, exc_type, exc_value, traceback):
        translation.activate(self.old_language)
