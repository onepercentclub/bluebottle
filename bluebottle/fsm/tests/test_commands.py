import sys
from io import StringIO

from django.core.management import call_command
from bluebottle.test.utils import BluebottleTestCase
from scripts.generate_states_documentation import dev_models


class PrintTransitionsTestCase(BluebottleTestCase):

    def print_transitions(self, model):
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        call_command(
            'print_transitions',
            model,
        )
        sys.stdout = old_stdout
        html = result.getvalue()
        html = html.encode('ascii', 'ignore')
        return html

    def test_print_transitions_all_models_render(self):
        for model in dev_models:
            html = self.print_transitions(model['model'])
            self.assertTrue(
                html.startswith(b'<h2>States</h2>'),
                "{} documentation should print without errors.".format(model['model'])
            )
            self.assertTrue(
                html.endswith(b'</table>\n'),
                "{} documentation should print without errors.".format(model['model'])
            )
