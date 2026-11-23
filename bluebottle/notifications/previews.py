import logging
import re

from django.template import Context, loader
from django.template.loader_tags import BLOCK_CONTEXT_KEY, BlockContext, BlockNode, ExtendsNode
from django.utils.translation import pgettext

from bluebottle.notifications.activity_messages import get_activity_actions
from bluebottle.time_based.models import ScheduleActivity
from bluebottle.utils.utils import get_current_language

logger = logging.getLogger(__name__)


class PreviewMember:

  def __init__(self, member=None):
        if team:
            placeholder = pgettext('platform-email', "[Team captain's first name]")
        else:
            placeholder = pgettext('platform-email', "[Participant's first name]")
        self.first_name = member.first_name if member else placeholder
        self.full_name = member.full_name if member else placeholder
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

    def __init__(self, activity, team=False, recipient=None):
        self.activity = activity
        self.user = PreviewMember(team=team)
        self.participants = EmptyQuery()
        slots = getattr(activity, 'slots', None)
        self.slot = slots.order_by('start').first() if slots is not None else None

    def __getattr__(self, name):
        if name.startswith('__') or name == 'activity':
            raise AttributeError(name)
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


def get_preview_slot(activity, slot):
    if slot and activity.slots.count() == 1:
        return {**slot, 'location': slot['location'] or pgettext('platform-email', '[Location]')}
    return {
        'title': '',
        'is_online': False,
        'online_meeting_url': None,
        'location': pgettext('platform-email', '[Location]'),
        'location_hint': '',
        'start_date': pgettext('platform-email', '[Date]'),
        'start_time': pgettext('platform-email', '[Time]'),
        'end_time': '',
        'timezone': '',
    }

  
def add_placeholders(activity, context):
    if 'slot' in context:
        context['slot'] = get_preview_slot(activity, context['slot'])


def is_team_activity(activity):
    return isinstance(activity, ScheduleActivity) and activity.team_activity == 'teams'


def get_message_class(activity, message_classes):
    if is_team_activity(activity):
        return message_classes[1]
    return message_classes[0]


def get_message_previews(activity, recipient=None):
    previews = []
    for action, message_classes in get_activity_actions(activity).items():
        message_class = get_message_class(activity, message_classes)
        obj = PreviewContributor(activity, recipient, team=is_team_activity(activity))
        message = message_class(obj)
        message.attachments = lambda recipient=None: None
        try:
            context = message.get_context(obj.user)
            add_placeholders(activity, context)
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
