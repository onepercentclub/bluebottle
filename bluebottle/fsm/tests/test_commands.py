import sys
from io import StringIO

from django.conf import settings
from django.core.management import call_command

from bluebottle.test.utils import BluebottleTestCase


class PrintTransitionsTestCase(BluebottleTestCase):

    def document_transitions(self, model):
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        call_command(
            'document_transitions',
            model,
        )
        sys.stdout = old_stdout
        html = result.getvalue()
        html = html.encode('ascii', 'ignore')
        return html

    def test_print_transitions_all_models_render(self):
        for model in settings.CONFLUENCE['dev_models']:
            data = eval(self.document_transitions(model['model']))
            self.assertEquals(
                [key for key in data.keys()],
                ['states', 'transitions', 'triggers', 'periodic_tasks']
            )
