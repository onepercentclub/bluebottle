import re
from django import template
from django.template.base import Node
from django.utils.functional import keep_lazy_text


register = template.Library()


@register.tag
def nobreaks(parser, token):
    nodelist = parser.parse(('endnobreaks',))
    parser.delete_first_token()
    return NoBreakNode(nodelist)


class NoBreakNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        strip_line_breaks = keep_lazy_text(
            lambda x: re.sub(r'[\n]+', '\n', x)
        )
        return strip_line_breaks(self.nodelist.render(context).strip())
