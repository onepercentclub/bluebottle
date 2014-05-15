# coding: utf-8
from django import template
from django.conf import settings
from django.template.base import TemplateSyntaxError, TextNode
from django.template.loader_tags import BlockNode
from django.utils.encoding import force_str
from django.utils.functional import Promise

""" based on django_templatetag_handlebars """


register = template.Library()


def verbatim_tags(parser, token, endtagname='', endtagnames=[]):
    """
    Javascript templates (jquery, handlebars.js, mustache.js) use constructs like:

    ::

        {{if condition}} print something{{/if}}

    This, of course, completely screws up Django templates,
    because Django thinks {{ and }} means something.

    The following code preserves {{ }} tokens.

    This version of verbatim template tag allows you to use tags
    like url {% url name %}. {% trans "foo" %} or {% csrf_token %} within.

    @returns a list of nodes.
    """
    nodelist = parser.create_nodelist()
    while 1:
        token = parser.tokens.pop(0)

        if token.contents in endtagnames or token.contents == endtagname:
            break

        # special case, {{ block.super }} is something we don't want to escape!
        # TODO: refactor this condition, token.split_contents should return
        # only one string, block.super, otherwise we might be dealing with
        # handlebars templating shenanigans

        # FIXME: block.super not working

        # if 'block.super' in token.contents:
        #     filter_expression = parser.compile_filter(token.contents)
        #     var_node = parser.create_variable_node(filter_expression)
        #     parser.extend_nodelist(nodelist, var_node, token)
        #     import pdb; pdb.set_trace()

        if token.token_type == template.TOKEN_VAR:
            parser.extend_nodelist(nodelist, TextNode('{{'), token)
            parser.extend_nodelist(nodelist, TextNode(token.contents), token)

        elif token.token_type == template.TOKEN_TEXT:
            parser.extend_nodelist(nodelist, TextNode(token.contents), token)

        elif token.token_type == template.TOKEN_BLOCK:
            try:
                command = token.contents.split()[0]
            except IndexError:
                parser.empty_block_tag(token)

            try:
                compile_func = parser.tags[command]
            except KeyError:
                parser.invalid_block_tag(token, command, None)
            try:
                node = compile_func(parser, token)
            except template.TemplateSyntaxError, e:
                if not parser.compile_function_error(token, e):
                    raise
            parser.extend_nodelist(nodelist, node, token)

        if token.token_type == template.TOKEN_VAR:
            parser.extend_nodelist(nodelist, TextNode('}}'), token)
    return nodelist


class VerbatimNode(template.Node):
    """
    Wrap {% verbatim %} and {% endverbatim %} around a
    block of javascript template and this will try its best
    to output the contents with no changes.

    ::

        {% verbatim %}
            {% trans "Your name is" %} {{first}} {{last}}
        {% endverbatim %}
    """
    def __init__(self, text_and_nodes):
        self.text_and_nodes = text_and_nodes

    def render(self, context):
        output = ""
        # If its text we concatenate it, otherwise it's a node and we render it
        for bit in self.text_and_nodes:
            if isinstance(bit, basestring):
                output += bit
            else:
                output += bit.render(context)
        return output

@register.tag
def bb_verbatim(parser, token):
    text_and_nodes = verbatim_tags(parser, token, 'endbb_verbatim')
    return VerbatimNode(text_and_nodes)


@register.tag('block_verbatim')
def do_block(parser, token):
    """
    Define a block that can be overridden by child templates. Adapted for handlebar
    template syntax. Note that you cannot use template variables in these blocks!
    """

    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' tag takes only one argument" % bits[0])
    block_name = bits[1]
    # Keep track of the names of BlockNodes found in this template, so we can
    # check for duplication.
    try:
        if block_name in parser.__loaded_blocks:
            raise TemplateSyntaxError("'%s' tag with name '%s' appears more than once" % (bits[0], block_name))
        parser.__loaded_blocks.append(block_name)
    except AttributeError: # parser.__loaded_blocks isn't a list yet
        parser.__loaded_blocks = [block_name]


    acceptable_endblocks = ('endblock_verbatim', 'endblock_verbatim %s' % block_name)

    # modify nodelist!
    nodelist = verbatim_tags(parser, token, endtagnames=acceptable_endblocks)

    return BlockNode(block_name, nodelist)


@register.simple_tag
def handlebars_js():
    return """<script src="%shandlebars.js"></script>""" % settings.STATIC_URL


class HandlebarsNode(VerbatimNode):
    """
    A Handlebars.js block is a *verbatim* block wrapped inside a
    named (``template_id``) <script> tag.

    ::

        {% tplhandlebars "tpl-popup" %}
            {{#ranges}}
                <li>{{min}} < {{max}}</li>
            {{/ranges}}
        {% endtplhandlebars %}

    """
    def __init__(self, template_id, text_and_nodes):
        super(HandlebarsNode, self).__init__(text_and_nodes)
        self.template_id = template_id

    def render(self, context):
        USE_EMBER_STYLE_ATTRS = getattr(settings, 'USE_EMBER_STYLE_ATTRS', False)
        output = super(HandlebarsNode, self).render(context)
        head_script = ('<script type="text/x-handlebars" data-template-name="%s">' if USE_EMBER_STYLE_ATTRS is True else '<script id="%s" type="text/x-handlebars-template">')%(self.template_id)
        return """
        %s
        %s
        </script>""" % (head_script, output)

@register.tag
def tplhandlebars(parser, token):
    text_and_nodes = verbatim_tags(parser, token, endtagname='endtplhandlebars')
    # Extract template id from token
    tokens = token.split_contents()
    stripquote = lambda s: s[1:-1] if s[:1]=='"' else s
    try:
        tag_name, template_id = map(stripquote , tokens[:2])
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires exactly one argument" % token.split_contents()[0]
    return HandlebarsNode(template_id, text_and_nodes)



@register.simple_tag
def bb_component(component, *args, **kwargs):
    """
    Template tag to generate Ember components with translated arguments.

    Usage: {% bb_component 'my-component' myFirstArg="'foo'" mySecondArg='bar' %}
    Translates to: {{my-component myFirstArg='foo' mySecondArg=bar}}
    """
    import sys
    reload(sys)
    sys.setdefaultencoding("utf8")

    if not isinstance(component, basestring) or not len(component):
        raise template.TemplateSyntaxError("bb-component tag requires at least one argument")

    component_bits = [component]
    bits = u''
    for key, value in kwargs.items():
        # trigger translation if we're dealing with Lazy translatable strings
        if isinstance(value, Promise):
            value = '\'{0}\''.format(force_str(value).replace("'", "\\'"))
        if key in ('name', 'type') or 'Binding' in key:
            value = '\'{0}\''.format(value)
        bit = u'{key}={value}'.format(key=key, value=value)
        bits += bit
        component_bits.append(bit)

    return u'{{' + u' '.join(component_bits) + '}}'

@register.tag(name='bb_block_component')
def do_bb_block_component(parser, token, *args, **kwargs):
    params = token.split_contents()
    params.pop(0)

    nodelist = parser.parse(('endbb_block_component',))
    parser.delete_first_token()

    component_bits = []
    for param in params:
        key, value = param.split('=')
        # trigger translation if we're dealing with Lazy translatable strings
        if isinstance(value, Promise):
            value = '\'{0}\''.format(force_str(value))
        # bit = '{key}={value}'.format(key=key, value=value)
        # component_bits.append(param)

    return BbBlockComponentNode(nodelist, component_bits)


class BbBlockComponentNode(template.Node):

    def __init__(self, nodelist, params=[]):
        self.nodelist = nodelist
        self.params = params

    def render(self, context):
        return '{{#bb-form-field ' + ' '.join(self.params) + ' }}' + self.nodelist.render(context) +'{{/bb-form-field}}'
