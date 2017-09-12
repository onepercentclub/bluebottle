from moneyed import Money

from django.test import TestCase
from django.template import Context, Template


class TagTests(TestCase):
    def _render(self, template, context):
        context = Context(context)
        return Template('{% load money %}' + template).render(context)

    def test_amount(self):
        self.assertEqual(
            self._render('{{ amount|format_money}}', {'amount': Money(10, 'USD')}),
            '$ 10'
        )
