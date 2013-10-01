from django.template import Template, Context, TemplateSyntaxError


import unittest


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
            t = Template(
                '{% block_verbatim test %}'
                '{{verbatim node}}'
                '{% endblock_verbatim %}'
                )
        self.assertRaises(TemplateSyntaxError, _create_template)