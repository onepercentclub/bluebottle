import logging
import re

from django.template import Context, loader
from django.template.loader_tags import BLOCK_CONTEXT_KEY, BlockContext, BlockNode, ExtendsNode
from django.utils.translation import pgettext

from bluebottle.notifications.activity_messages import get_activity_actions
from bluebottle.utils.utils import get_current_language

logger = logging.getLogger(__name__)


class PreviewMember:
    def __init__(self):
        self.first_name = pgettext('platform-email', "[name]")
        self.full_name = pgettext('platform-email', "[name]")
        self.primary_language = get_current_language()
        self.email = ''


class EmptyQuery(list):
    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self


class PreviewContributor:
    pk = None
    id = None
    team = None
    answer = None

    def __init__(self, activity):
        self.activity = activity
        self.user = PreviewMember()
        self.participants = EmptyQuery()
        slots = getattr(activity, 'slots', None)
        self.slot = slots.order_by('start').first() if slots is not None else None

    def __getattr__(self, name):
        return getattr(self.activity, name)


class MessagePreview:
    def __init__(self, activity, action, subject, body, action_title):
        self.pk = self.id = '{}-{}'.format(activity.pk, action)
        self.action = action
        self.subject = subject
        self.body = body
        self.action_title = action_title


def render_block(template_name, block_name, context):
    """Render a single block of a template, following its {% extends %} chain."""
    template = loader.get_template(template_name).template
    context = Context(context)
    with context.render_context.push_state(template), context.bind_template(template):
        block_context = BlockContext()
        context.render_context[BLOCK_CONTEXT_KEY] = block_context
        nodelist = template.nodelist
        while True:
            block_context.add_blocks({
                node.name: node for node in nodelist.get_nodes_by_type(BlockNode)
            })
            extends = nodelist.get_nodes_by_type(ExtendsNode)
            if not extends:
                break
            nodelist = extends[0].get_parent(context).nodelist

        html = block_context.blocks[block_name][0].render(context)
        return re.sub(r'\s*\n\s*', '\n', html).strip()


def get_message_class(activity, message_classes):
    if len(message_classes) > 1 and getattr(activity, 'team_activity', None) == 'teams':
        return message_classes[1]
    return message_classes[0]


def get_message_previews(activity):
    previews = []
    for action, message_classes in get_activity_actions(activity).items():
        message_class = get_message_class(activity, message_classes)
        obj = PreviewContributor(activity)
        message = message_class(obj)
        message.attachments = lambda recipient=None: None
        try:
            context = message.get_context(obj.user)
            previews.append(MessagePreview(
                activity,
                action,
                str(message.subject).format(**context),
                render_block('mails/{}.html'.format(message.template), 'content', context),
                str(context.get('action_title') or ''),
            ))
        except Exception:
            logger.exception('Could not preview %s for activity %s', message_class.__name__, activity.pk)
    return previews
