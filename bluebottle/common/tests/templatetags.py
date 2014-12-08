from django.template import Template, Context, TemplateSyntaxError
from django.utils import unittest


class BlockVerbatimTestCase(unittest.TestCase):
    """
    Testcase testing the block_verbatim template tag.

    block_verbatim parses other template tags while leaving {{foo}} structures
    untouched. {% block %} inside block_verbatim DOES render context variables.
    """

    def test_render(self):
        """ Test block_verbatim with block name in closing tag """
        t = Template(
            '{% load bb_ember %}' # load the tag library
            '{% block_verbatim test %}'
            '{{verbatim node}}'
            '{% endblock_verbatim test %}'
            )
        rendered = t.render(Context())

        self.assertEqual(rendered, u'{{verbatim node}}')

    def test_render_no_name_closing_tag(self):
        """ Test block_verbatim without block name in closing tag """
        t = Template(
            '{% load bb_ember %}' # load the tag library
            '{% block_verbatim test %}'
            '{{verbatim node}}'
            '{% endblock_verbatim %}'
            )
        rendered = t.render(Context())

        self.assertEqual(rendered, u'{{verbatim node}}')

    def test_block_in_block(self):
        t = Template(
            '{% load bb_ember %}' # load the tag library
            '{% block_verbatim test %}'
            '{{verbatim node}}'
            '{% block foo %}'
            '\nfoo'
            '{% endblock %}'
            '{% endblock_verbatim %}'
            )
        rendered = t.render(Context())

        self.assertEqual(rendered, u'{{verbatim node}}\nfoo')

    def test_block_in_block_with_context(self):
        t = Template(
            '{% load bb_ember %}' # load the tag library
            '{% block_verbatim test %}'
            '{{verbatim node}}'
            '{% block foo %}'
            '\n{{ foo }}'
            '{% endblock %}'
            '{% endblock_verbatim %}'
            )
        c = Context({'foo': 'bar'})
        rendered = t.render(c)

        self.assertEqual(rendered, u'{{verbatim node}}\nbar')

    def test_tag_not_loaded(self):
        def _create_template():
            Template(
                '{% block_verbatim test %}'
                '{{verbatim node}}'
                '{% endblock_verbatim %}'
                )
        self.assertRaises(TemplateSyntaxError, _create_template)


class BBComponentTestCase(unittest.TestCase):
    """
    TestCase testing the correct functioning of the bb_component tag.

    bb_component takes an arbitrary number of keyword arguments and translates
    strings marked for translation.
    """

    def setUp(self):
        self.load_statement = "{% load bb_ember %}";

    def test_no_component_args(self):
        t = Template(
            self.load_statement +
            '{% bb_component \'my-component\' %}'
            )
        rendered = t.render(Context())
        self.assertEqual(rendered, u'{{my-component}}')

    def test_no_args(self):
        """ Test that a TemplateSyntaxError is raised when no component name is specified (as a string)"""
        def _create_template():
            t = Template(
                self.load_statement +
                '{% bb_component %}'
                )
            t.render(Context())
        self.assertRaises(TemplateSyntaxError, _create_template)

        def _create_template2():
            t = Template(
                self.load_statement +
                '{% bb_component foo %}'
                )
            t.render(Context())
        self.assertRaises(TemplateSyntaxError, _create_template2)

    def test_kwargs(self):
        """ Test that the keyword arguments are indeed in the component """
        t = Template(
            self.load_statement +
            '{% bb_component \'my-component\' value1=\'foo\' name=\'bar\' valueBinding=\'title\' errors=\'foobar\' %}'
            )
        result = t.render(Context())

        self.assertTrue(result.startswith('{{my-component '))
        self.assertIn('value1=foo', result)
        self.assertIn('name=\'bar\'', result)
        self.assertIn('valueBinding=\'title\'', result)
        self.assertIn('errors=foobar', result)
        self.assertTrue(result.endswith('}}'))
