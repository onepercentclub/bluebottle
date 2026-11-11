"""
Generate clickable HTML documentation for finite state machines.

Responsibilities are split as follows:

- Introspection helpers in this module build a plain Python ``doc`` structure
  describing states, transitions, triggers and periodic tasks for each model.
- ``render_html`` turns that structure into a template context and renders a
  Django template (HTML lives in ``templates/fsm/fsm_documentation.html``).
- Styling is served from a static CSS file
  (``static/fsm/fsm_documentation.css``).
- Graphs are built by ``bluebottle.fsm.docs_graphs`` as DOT and rendered in
  the browser by viz.js, so no graphviz binary is needed.

This command does not require database queries for state-machine inspection;
it uses class introspection only.
"""
import json
import re
from collections import OrderedDict
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from bluebottle.fsm import docs_graphs
from bluebottle.fsm.effects import BaseTransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger
from bluebottle.fsm.utils import get_doc, setup_instance


def _effect_notification_detail(effect_cls, instance=None):
    """If effect is NotificationEffect, return message class name, subject, template, docstring, recipients."""
    if getattr(effect_cls, '__name__', '') != '_NotificationEffect' and not hasattr(effect_cls, 'message'):
        return None
    message_cls = getattr(effect_cls, 'message', None)
    if message_cls is None:
        return None
    recipients_doc = None
    if hasattr(message_cls, 'get_recipients'):
        rec_doc = get_doc(message_cls.get_recipients)
        if rec_doc and '(documentation missing)' not in str(rec_doc):
            recipients_doc = rec_doc
    template_path = getattr(message_cls, 'template', '')
    template_rendered = None
    if template_path and instance is not None:
        try:
            message = message_cls(instance)
            template_rendered = getattr(message, 'generic_content_html', None) or getattr(
                message, 'generic_content', None
            )
            if template_rendered is not None:
                template_rendered = str(template_rendered)
        except Exception:
            template_rendered = None
    msg_doc = get_doc(message_cls)
    return {
        'message_class': getattr(message_cls, '__name__', str(message_cls)),
        'subject': getattr(message_cls, 'subject', ''),
        'template': template_path,
        'message_doc': msg_doc,
        'show_message_doc': bool(msg_doc and '(documentation missing)' not in str(msg_doc)),
        'recipients_doc': recipients_doc,
        'template_rendered': template_rendered,
    }


def _effect_transition_detail(effect_cls):
    """If effect is TransitionEffect (same-model transition), return transition name, target, sources."""
    if hasattr(effect_cls, 'transition_effect_class'):
        return None
    if not hasattr(effect_cls, 'transition'):
        return None
    transition = getattr(effect_cls, 'transition', None)
    if transition is None:
        return None
    target = getattr(transition, 'target', None)
    target_name = getattr(target, 'name', '').capitalize() if target else ''
    transition_name = getattr(transition, 'name', '')
    sources = getattr(transition, 'sources', ())
    source_names = [getattr(s, 'name', str(s)).capitalize() for s in sources]
    return {
        'transition_name': transition_name,
        'target': target_name,
        'sources': source_names,
    }


def _effect_related_detail(effect_cls):
    """If effect is RelatedTransitionEffect, return relation name and transition (name, target, sources)."""
    if not hasattr(effect_cls, 'transition_effect_class') or not hasattr(effect_cls, 'relation'):
        return None
    te = getattr(effect_cls, 'transition_effect_class', None)
    if te is None:
        return None
    transition = getattr(te, 'transition', None)
    if transition is None:
        return None
    relation = getattr(effect_cls, 'relation', '')
    target = getattr(transition, 'target', None)
    target_name = getattr(target, 'name', '').capitalize() if target else ''
    transition_name = getattr(transition, 'name', '')
    sources = getattr(transition, 'sources', ())
    source_names = [getattr(s, 'name', str(s)).capitalize() for s in sources]
    return {
        'relation': relation,
        'transition_name': transition_name,
        'target': target_name,
        'sources': source_names,
    }


def _effect_clarification(effect_cls):
    """
    Return a short clarification string for an effect: __doc__ (first line) or
    the effect's description attribute (e.g. RelatedTransitionEffect(..., description=...)).
    """
    doc = getattr(effect_cls, '__doc__', None)
    if doc and isinstance(doc, str):
        first = doc.strip().split('\n')[0].strip()
        if first and '(documentation missing)' not in first:
            return re.sub(r'\s+', ' ', first)
    desc = getattr(effect_cls, 'description', None)
    if desc and isinstance(desc, str) and desc.strip():
        return re.sub(r'\s+', ' ', str(desc).strip())
    return None


def _effect_docstring(effect_cls):
    """
    Return effect description: use __doc__ when present and meaningful,
    then description attribute, otherwise generate one from the effect logic.
    """
    doc = get_doc(effect_cls)
    if doc and '(documentation missing)' not in str(doc):
        return re.sub(r'\s+', ' ', str(doc).strip())
    clarification = _effect_clarification(effect_cls)
    if clarification:
        return clarification
    # Generate from logic
    if hasattr(effect_cls, 'transition') and not hasattr(effect_cls, 'transition_effect_class'):
        tr = getattr(effect_cls, 'transition', None)
        if tr:
            target = getattr(tr, 'target', None)
            target_name = getattr(target, 'name', '').capitalize() if target else ''
            tname = getattr(tr, 'name', '')
            sources = getattr(tr, 'sources', ())
            if sources:
                source_names = [getattr(s, 'name', str(s)).capitalize() for s in sources]
                return "Execute transition '{}' to state {} (from {}).".format(
                    tname, target_name, ' | '.join(source_names))
            return "Execute transition '{}' to state {}.".format(tname, target_name)
    if hasattr(effect_cls, 'transition_effect_class') and hasattr(effect_cls, 'relation'):
        rel = getattr(effect_cls, 'relation', '')
        te = getattr(effect_cls, 'transition_effect_class', None)
        tr = getattr(te, 'transition', None) if te else None
        if tr:
            target = getattr(tr, 'target', None)
            target_name = getattr(target, 'name', '').capitalize() if target else ''
            tname = getattr(tr, 'name', '')
            return "Execute transition '{}' to state {} on related '{}'.".format(tname, target_name, rel)
    if hasattr(effect_cls, 'message'):
        msg = getattr(effect_cls, 'message', None)
        if msg:
            msg_name = getattr(msg, '__name__', str(msg))
            subject = getattr(msg, 'subject', '')
            if subject:
                return "Send notification {} (subject: {}).".format(msg_name, subject)
            return "Send notification {}.".format(msg_name)
    name = getattr(effect_cls, '__name__', str(effect_cls))
    if name and not name.startswith('_'):
        return "Effect: {}.".format(name)
    return None


def _format_effect_summary(effect_cls, cond_str):
    """
    Build one-line summary for an effect (transition/related/notification/other).
    Append clarification from __doc__/description when present.
    """
    name = getattr(effect_cls, '__name__', str(effect_cls))
    base = None
    if hasattr(effect_cls, 'transition') and not hasattr(effect_cls, 'transition_effect_class'):
        tr = getattr(effect_cls, 'transition', None)
        target = getattr(tr, 'target', None) if tr else None
        target_name = getattr(target, 'name', '').capitalize() if target else ''
        transition_name = getattr(tr, 'name', '') if tr else ''
        base = "Transition: {} to {}".format(transition_name, target_name) + (' if ' + cond_str if cond_str else '')
    elif hasattr(effect_cls, 'transition_effect_class'):
        te = getattr(effect_cls, 'transition_effect_class', None)
        tr = getattr(te, 'transition', None) if te else None
        target = getattr(tr, 'target', None) if tr else None
        target_name = getattr(target, 'name', '').capitalize() if target else ''
        transition_name = getattr(tr, 'name', '') if tr else ''
        rel = getattr(effect_cls, 'relation', '')
        base = "Relation '{}' → {} to {}".format(rel, transition_name, target_name)
        base += (' if ' + cond_str if cond_str else '')
    elif hasattr(effect_cls, 'message'):
        msg = getattr(effect_cls, 'message', None)
        msg_name = getattr(msg, '__name__', str(msg)) if msg else name
        base = 'Send {}'.format(msg_name) + (' if ' + cond_str if cond_str else '')
    else:
        base = name + (' if ' + cond_str if cond_str else '')
    clarification = _effect_clarification(effect_cls)
    if clarification and len(clarification) <= 120:
        return '{} — {}'.format(base, clarification)
    return base


def _is_redundant_effect_doc(doc_str, detail):
    """True if doc_str is auto-generated and we already show the same info in transition/related/notification detail."""
    if not doc_str:
        return True
    doc_str = str(doc_str).strip()
    # Same as _effect_docstring: "Execute transition 'X' to state Y (from Z)." or "Execute transition 'X' to state Y."
    if detail.get('transition') and (
        re.match(r"Execute transition '[^']+' to state [^.]+ \(from [^)]+\)\.", doc_str)
        or re.match(r"Execute transition '[^']+' to state [^.]+\.$", doc_str)
    ):
        return True
    # Same as generated "Execute transition 'X' to state Y on related 'Z'."
    if detail.get('related') and re.match(
        r"Execute transition '[^']+' to state [^.]+ on related '[^']+'\.", doc_str
    ):
        return True
    # Same as generated "Send notification X (subject: Y)." or
    # "Send notification X." — subject shown in notification block
    if detail.get('notification') and (
        re.match(r"Send notification [^.]+ \(subject: [^)]+\)\.", doc_str)
        or re.match(r"Send notification [^.]+\.$", doc_str)
    ):
        return True
    return False


def get_state_id(state):
    """Id for a state (value or name)."""
    v = getattr(state, 'value', None) or getattr(state, 'name', '')
    return (v if v else 'empty').replace(' ', '-')


def get_transition_id(transition):
    """Id for a transition (field name)."""
    return getattr(transition, 'field', str(transition.name)).replace(' ', '-')


def _relation_applies(model, effect_cls):
    relation = getattr(effect_cls, 'relation', '')
    return not relation or hasattr(model, relation.split('.')[0])


def _humanize(name):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', name.strip('_')).capitalize()


def _relation_from_name(effect_cls):
    """``_ActiveDurationsTransitionEffect`` changes ``active_durations``."""
    name = re.sub(r'TransitionEffect$', '', effect_cls.__name__.strip('_'))
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def _effect_graph_info(model, effect_cls, cond_str, notification):
    """Short description of an effect for the effect graphs; None when it never applies to ``model``."""
    base_id = model._meta.model_name
    transition = getattr(effect_cls, 'transition', None)
    if hasattr(effect_cls, 'transition_effect_class') or (
        transition is not None and not issubclass(effect_cls, BaseTransitionEffect)
    ):
        if not _relation_applies(model, effect_cls):
            return None
        if hasattr(effect_cls, 'transition_effect_class'):
            relation = effect_cls.relation
            transition = effect_cls.transition_effect_class.transition
        else:
            relation = _relation_from_name(effect_cls)
        return {
            'kind': 'related',
            'label': '{} → {}'.format(relation, transition.name),
            'conditions': cond_str,
            'relation': relation,
            'transition': transition,
        }
    if transition is not None:
        return {
            'kind': 'own',
            'label': '{} → {}'.format(transition.name, transition.target.name.capitalize()),
            'url': '#{}-trans-{}'.format(base_id, get_transition_id(transition)),
            'conditions': cond_str,
            'transition': transition,
        }
    if notification:
        tooltip = notification['message_class']
        if notification.get('recipients_doc'):
            tooltip += ' to ' + notification['recipients_doc']
        return {
            'kind': 'notification',
            'label': notification['message_class'],
            'tooltip': tooltip,
            'conditions': cond_str,
        }
    app = effect_cls.__module__.split('.')[1] if effect_cls.__module__.startswith('bluebottle.') else ''
    label = _effect_clarification(effect_cls) or _humanize(effect_cls.__name__)
    return {
        'kind': 'other',
        'label': '{}: {}'.format(app.replace('_', ' ').capitalize(), label) if app else label,
        'conditions': cond_str,
    }


def _describe_effect(model, effect_cls, instance):
    try:
        conds = getattr(effect_cls, 'conditions', None) or []
        cond_str = ' and '.join([get_doc(c) for c in conds])
        summary = _format_effect_summary(effect_cls, cond_str)
        detail = {
            'doc': _effect_docstring(effect_cls),
            'notification': _effect_notification_detail(effect_cls, instance=instance),
            'transition': _effect_transition_detail(effect_cls),
            'related': _effect_related_detail(effect_cls),
        }
        graph = _effect_graph_info(model, effect_cls, cond_str, detail['notification'])
        if not any([detail['doc'], detail['notification'], detail['transition'], detail['related']]):
            detail = None
        else:
            detail['show_doc'] = not _is_redundant_effect_doc(detail.get('doc'), detail)
        if graph is None:
            summary += ' (relation does not exist on this model, so this never runs)'
        return {'summary': summary, 'detail': detail, 'graph': graph, 'effect_cls': effect_cls}
    except Exception:
        return {
            'summary': getattr(effect_cls, '__name__', str(effect_cls)),
            'detail': None, 'graph': None, 'effect_cls': effect_cls,
        }


def document_fsm_from_classes(model):
    """
    Build FSM documentation from model/state machine/trigger classes only.
    No instance creation, so no database access.
    """
    machine_class = model._state_machines.get('states')
    if not machine_class:
        return {'states': [], 'transitions': [], 'triggers': []}
    try:
        instance = setup_instance(model)
    except Exception:
        instance = None
    states = list(machine_class.states.values())
    transitions = list(machine_class.transitions.values())
    doc = {
        'states': [
            {
                'name': s.name.capitalize() if getattr(s, 'name', None) else str(s),
                'description': getattr(s, 'description', '') or '',
                'value': getattr(s, 'value', ''),
                'id': get_state_id(s),
            }
            for s in states
        ],
        'transitions': [],
        'triggers': [],
        'periodic_tasks': [],
    }
    known = {s['id'] for s in doc['states']}
    for transition in transitions:
        for state in list(transition.sources) + [transition.target]:
            state_id = get_state_id(state)
            if state_id not in known and state_id != 'all':
                known.add(state_id)
                doc['states'].append({
                    'name': str(state.name).capitalize(),
                    'description': getattr(state, 'description', '') or '',
                    'value': getattr(state, 'value', ''),
                    'id': state_id,
                })

    for transition in transitions:
        triggers_for_trans = [
            t for t in model.triggers.triggers
            if isinstance(t, TransitionTrigger) and t.transition == transition
        ]
        effects = [
            _describe_effect(model, effect_cls, instance)
            for t in triggers_for_trans for effect_cls in t.effects
        ]
        doc['transitions'].append({
            'name': str(transition.name),
            'description': transition.description or '',
            'from_states': [s.name.capitalize() for s in transition.sources],
            'from_ids': [get_state_id(s) for s in transition.sources],
            'to': transition.target.name.capitalize(),
            'to_id': get_state_id(transition.target),
            'manual': 'Automatic' if transition.automatic else 'Manual',
            'conditions': [get_doc(c) for c in transition.conditions],
            'effects': effects,
            'id': get_transition_id(transition),
            'field': getattr(transition, 'field', ''),
            'permission_doc': get_doc(transition.permission) if getattr(transition, 'permission', None) else None,
            'caused_by': [],
        })
    # caused_by: triggers that are not TransitionTrigger(this) but have an effect for this transition
    transition_by_id = {id(t): i for i, t in enumerate(transitions)}
    for trigger in model.triggers.triggers:
        for effect_cls in trigger.effects:
            transition = None
            if hasattr(effect_cls, 'transition'):
                transition = getattr(effect_cls, 'transition', None)
            if transition is None and hasattr(effect_cls, 'transition_effect_class'):
                te = getattr(effect_cls, 'transition_effect_class', None)
                if te and hasattr(te, 'transition'):
                    transition = te.transition
            if transition is None:
                continue
            if hasattr(effect_cls, 'transition_effect_class'):
                # A related effect changes another object, not this one.
                continue
            if isinstance(trigger, TransitionTrigger) and trigger.transition == transition:
                continue
            idx = transition_by_id.get(id(transition))
            if idx is not None:
                conds = getattr(effect_cls, 'conditions', None) or []
                cond_docs = [get_doc(c) for c in conds]
                doc['transitions'][idx]['caused_by'].append({
                    'trigger': str(trigger),
                    'conditions': cond_docs,
                    'effect_name': getattr(effect_cls, '__name__', str(effect_cls)),
                })
    # Other triggers (not TransitionTrigger)
    for trigger in model.triggers.triggers:
        if isinstance(trigger, TransitionTrigger):
            continue
        doc['triggers'].append({
            'when': str(trigger),
            'effects': [_describe_effect(model, effect_cls, instance) for effect_cls in trigger.effects],
            'id': re.sub(r'[^a-z0-9]+', '-', str(trigger).lower().strip()).strip('-'),
        })
    # Periodic tasks (model.periodic_tasks)
    for task_cls in getattr(model, 'periodic_tasks', []) or []:
        task_name = getattr(task_cls, '__name__', str(task_cls))
        task_doc = get_doc(task_cls)
        if task_doc and '(documentation missing)' in str(task_doc):
            task_doc = None
        doc['periodic_tasks'].append({
            'name': task_name,
            'id': re.sub(r'[^a-z0-9]+', '-', task_name.lower()).strip('-') or 'task',
            'description': task_doc,
            'effects': [
                _describe_effect(model, effect_cls, instance)
                for effect_cls in getattr(task_cls, 'effects', []) or []
            ],
        })
    return doc


def document_fsm_enriched(model):
    """
    Like document_model but with state/transition ids and
    for each transition: list of other triggers that can cause it (e.g. model field change).
    Uses class-only introspection so no DB is required.
    """
    return document_fsm_from_classes(model)


FAMILIES = OrderedDict([
    ('Date activities', ['DateActivity', 'DateActivitySlot', 'DateRegistration', 'DateParticipant']),
    ('Registered date activities', ['RegisteredDateActivity', 'RegisteredDateParticipant']),
    ('Deadline activities', ['DeadlineActivity', 'DeadlineRegistration', 'DeadlineParticipant']),
    ('Periodic activities', ['PeriodicActivity', 'PeriodicSlot', 'PeriodicRegistration', 'PeriodicParticipant']),
    ('Schedule activities', [
        'ScheduleActivity', 'ScheduleSlot', 'ScheduleRegistration', 'ScheduleParticipant',
        'Team', 'TeamMember', 'TeamScheduleSlot', 'TeamScheduleRegistration', 'TeamScheduleParticipant',
    ]),
])
SHARED_MODELS = {
    'TimeContribution': [
        'Date activities', 'Registered date activities', 'Deadline activities',
        'Periodic activities', 'Schedule activities',
    ],
}
APP_FAMILIES = {'funding_stripe': 'funding'}


def get_families(model):
    """Families (activity types) a model belongs to; falls back to its app."""
    name = model.__name__
    if name in SHARED_MODELS:
        return set(SHARED_MODELS[name])
    for family, members in FAMILIES.items():
        if name in members:
            return {family}
    app_label = model._meta.app_label
    return {APP_FAMILIES.get(app_label, app_label)}


def get_primary_family(model):
    name = model.__name__
    if name in SHARED_MODELS:
        return 'Time contributions'
    family = sorted(get_families(model))[0]
    return family if family in FAMILIES else family.replace('_', ' ').capitalize()


def _related_model(model, relation):
    for part in relation.split('.'):
        try:
            model = model._meta.get_field(part).related_model
        except Exception:
            return None
        if model is None:
            return None
    return model


def resolve_related_targets(model, relation, transition, owners):
    """
    Documented models whose state machine holds the transition a related effect fires.

    Related effects are declared on base classes and walk properties as well as fields,
    so the relation alone often points at an abstract base. The transition object
    is what the effect checks at runtime, so start from the models that own it and
    narrow down by relation and by activity family.
    """
    candidates = owners.get(id(transition), [])
    related = _related_model(model, relation)
    if related is not None:
        narrowed = [c for c in candidates if issubclass(c, related)]
        if narrowed:
            candidates = narrowed
    families = get_families(model)
    same_family = [c for c in candidates if get_families(c) & families]
    if same_family:
        return same_family
    return candidates if len(candidates) == 1 else []


def build_graph_index(fsm_entries):
    """
    Resolve related effects to documented models and collect, per transition, what it can cause.

    Returns ``{(base_id, transition_id): {...}}`` as used by :func:`docs_graphs.cascade_graph`,
    and fills in link targets and incoming edges on the docs.
    """
    owners = {}
    for model, _ in fsm_entries:
        for transition in model._state_machines['states'].transitions.values():
            owners.setdefault(id(transition), []).append(model)

    labels = {model._meta.model_name: str(model._meta.verbose_name) for model, _ in fsm_entries}
    index = {}
    for model, doc in fsm_entries:
        base_id = model._meta.model_name
        for transition in doc['transitions']:
            key = (base_id, transition['id'])
            entry = {
                'model': str(model._meta.verbose_name).capitalize(),
                'name': transition['name'],
                'url': '#{}-trans-{}'.format(base_id, transition['id']),
                'notifications': 0,
                'related': [],
            }
            for effect in transition['effects']:
                info = effect['graph']
                if not info:
                    continue
                if info['kind'] == 'notification':
                    entry['notifications'] += 1
                elif info['kind'] == 'own':
                    entry['related'].append({
                        'relation': 'self', 'conditions': info.get('conditions'),
                        'targets': [(base_id, get_transition_id(info['transition']))],
                    })
                elif info['kind'] == 'related':
                    target_transition = info['transition']
                    targets = [
                        (target._meta.model_name, get_transition_id(target_transition))
                        for target in resolve_related_targets(model, info['relation'], target_transition, owners)
                    ]
                    if targets:
                        names = [labels[target_base] for target_base, _ in targets]
                        info['url'] = '#{}-trans-{}'.format(*targets[0])
                        info['tooltip'] = '{} on {}'.format(target_transition.name, ', '.join(names))
                        info['label'] += ' ({})'.format(names[0] if len(names) == 1 else 'several models')
                    entry['related'].append({
                        'relation': info['relation'], 'conditions': info.get('conditions'),
                        'targets': targets,
                    })
            index[key] = entry

    docs = {model._meta.model_name: doc for model, doc in fsm_entries}
    for (base_id, transition_id), entry in index.items():
        for related in entry['related']:
            if related['relation'] == 'self':
                continue
            for target_base, target_id in related['targets']:
                for transition in docs[target_base]['transitions']:
                    if transition['id'] == target_id:
                        transition.setdefault('incoming', []).append({
                            'label': '{}: {}'.format(entry['model'], entry['name']),
                            'url': entry['url'],
                            'conditions': related['conditions'],
                        })
    for doc in docs.values():
        for transition in doc['transitions']:
            transition.setdefault('incoming', [])
            for cause in transition['caused_by']:
                transition['incoming'].append({
                    'label': cause['trigger'],
                    'conditions': ' and '.join(cause['conditions']),
                })
    return index


def get_fsm_models_for_apps(app_labels):
    """
    Return list of model classes that have a 'states' state machine in the given apps.
    Only includes models that explicitly set include_in_documentation = True.
    Each model is only included once (by class), sorted by app label then model name.
    Imports each app's states (and triggers) so @register() has run and models have _state_machines.
    """
    import importlib
    from django.apps import apps

    seen = set()
    result = []
    for app_label in app_labels:
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            continue
        # Ensure state machines and periodic_tasks are registered
        for mod in ('states', 'triggers', 'periodic_tasks'):
            try:
                importlib.import_module('{}.{}'.format(app_config.name, mod))
            except (ImportError, AttributeError):
                pass
        for model in app_config.get_models():
            if model in seen:
                continue
            if not getattr(model, '_state_machines', None):
                continue
            if 'states' not in model._state_machines:
                continue
            if model.__dict__.get('include_in_documentation') is not True:
                continue
            seen.add(model)
            result.append(model)
    result.sort(key=lambda m: (m._meta.app_label, m._meta.model_name))
    return result


def _state_links_from_doc(doc, base_id):
    """
    Build per-state from/to transition links (structured data for the template).
    Returns dict: state_name -> {'from_transitions': [(trans_name, trans_id)],
    'to_transitions': [(trans_name, trans_id)]}.
    """
    result = {}
    for t in doc.get('transitions', []):
        trans_id = '{}-trans-{}'.format(base_id, t.get('id', ''))
        trans_name = t.get('name', '')
        for from_s in t.get('from_states', []):
            result.setdefault(
                from_s,
                {'from_transitions': [], 'to_transitions': []}
            )['from_transitions'].append((trans_name, trans_id))
        to_s = t.get('to', '')
        result.setdefault(
            to_s,
            {'from_transitions': [], 'to_transitions': []}
        )['to_transitions'].append((trans_name, trans_id))
    return result


def _script_json(value):
    """JSON that is safe inside a <script> element."""
    return json.dumps(value).replace('</', '<\\/')


def _section_graphs(base_id, doc, index):
    for transition in doc['transitions']:
        effects = docs_graphs.effects_graph(transition, base_id)
        transition['effects_dot'] = _script_json(docs_graphs.to_dot(effects)) if effects else None
        cascade = docs_graphs.cascade_graph(index, (base_id, transition['id']))
        has_cascade = cascade and len(cascade['clusters']) > 1
        transition['cascade_dot'] = _script_json(docs_graphs.to_dot(cascade)) if has_cascade else None
        transition['cascade_truncated'] = cascade['truncated'] if has_cascade else 0
    lifecycle = docs_graphs.lifecycle_graph(doc, base_id)
    return {
        'lifecycle_dots': _script_json(docs_graphs.lifecycle_variants(doc, base_id)),
        'globals': lifecycle['globals'],
        'edges_before': docs_graphs.edge_count(doc, collapsed=False),
        'edges_after': docs_graphs.edge_count(doc, collapsed=True),
    }


def render_html(fsm_entries, viz_script=None):
    """
    Render the FSM documentation page using a Django template.

    ``fsm_entries`` is a list of ``(model_class, doc_dict)`` where
    ``doc_dict`` comes from :func:`document_fsm_enriched`.
    ``viz_script`` is the viz.js source to inline; when empty the page loads it from a CDN.
    """
    if not fsm_entries:
        return ''

    index = build_graph_index(fsm_entries)

    groups = OrderedDict()
    for model, doc in fsm_entries:
        model_name = model._meta.model_name
        verbose_name = model._meta.verbose_name
        family = get_primary_family(model)

        class_path = f'{model.__module__}.{model.__name__}'
        model_doc = getattr(model, '__doc__', None)
        if model_doc and isinstance(model_doc, str) and model_doc.strip():
            model_doc = re.sub(r'\s+', ' ', model_doc.strip())
        else:
            model_doc = ''

        section = {
            'base_id': model_name,
            'label': verbose_name,
            'class_path': class_path,
            'model_doc': model_doc,
            'doc': doc,
            'state_links': _state_links_from_doc(doc, model_name),
        }
        section.update(_section_graphs(model_name, doc, index))
        groups.setdefault(family, []).append(section)

    family_order = list(FAMILIES) + ['Time contributions']
    ordered = sorted(
        groups.items(),
        key=lambda item: (family_order.index(item[0]) if item[0] in family_order else len(family_order), item[0])
    )
    group_list = []
    for family, sections in ordered:
        family_id = 'family-' + re.sub(r'[^a-z0-9]+', '-', family.lower()).strip('-')
        members = [(s['base_id'], str(s['label']).capitalize()) for s in sections]
        family_graph = docs_graphs.family_map(members, index)
        group_list.append({
            'id': family_id,
            'label': family,
            'sections': sections,
            'map_dot': _script_json(docs_graphs.to_dot(family_graph)) if family_graph else None,
        })

    apps_label = ', '.join(sorted(set(m._meta.app_label for m, _ in fsm_entries)))
    title = 'FSM documentation – ' + apps_label

    # Inline CSS so the generated HTML is fully self‑contained.
    # Command lives in ``fsm/management/commands``; static file is in ``fsm/static/fsm``.
    app_root = Path(__file__).resolve().parent.parent.parent
    css_path = app_root / "static" / "fsm" / "fsm_documentation.css"
    try:
        inline_css = css_path.read_text(encoding="utf-8")
    except OSError:
        inline_css = ""

    context = {
        'title': title,
        'apps_label': apps_label,
        'groups': group_list,
        'inline_css': inline_css,
        'viz_script': viz_script,
        'viz_url': VIZ_URL,
    }

    return render_to_string('fsm/fsm_documentation.html', context)


VIZ_URL = 'https://cdn.jsdelivr.net/npm/@viz-js/viz@3.31.0/dist/viz-global.js'
VIZ_CACHE = Path(__file__).resolve().parent.parent.parent / 'static' / 'fsm' / 'vendor' / 'viz-global.js'


def load_viz_script():
    if not VIZ_CACHE.exists():
        VIZ_CACHE.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(VIZ_URL, timeout=30)
        response.raise_for_status()
        VIZ_CACHE.write_text(response.text, encoding='utf-8')
    return VIZ_CACHE.read_text(encoding='utf-8').replace('</script', '<\\/script')


class Command(BaseCommand):
    help = (
        'Generate clickable HTML documentation for FSM models (states, transitions, '
        'triggers, conditions, effects) with lifecycle, effect and cascade graphs. By default includes '
        'deeds, funding, funding_stripe, collect, grant_management, time_based, initiatives. '
        'Use --app to limit to specific app(s). No DB required.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='fsm_documentation.html',
            help='Output HTML file path (default: fsm_documentation.html)',
        )
        parser.add_argument(
            '--app', '-a',
            type=str,
            action='append',
            dest='apps',
            metavar='APP',
            help=(
                'App label(s) to document. Can be repeated. Default: deeds, funding, '
                'funding_stripe, collect, grant_management, time_based, initiatives.'
            ),
        )
        parser.add_argument(
            '--offline',
            action='store_true',
            help='Inline the graph renderer (viz.js) so the page works without network access.',
        )

    def handle(self, *args, **options):
        app_labels = options.get('apps')
        if not app_labels:
            app_labels = [
                'deeds',
                'funding',
                'funding_stripe',
                'collect',
                'grant_management',
                'time_based',
                'initiatives',
            ]

        models = get_fsm_models_for_apps(app_labels)
        if not models:
            self.stdout.write(self.style.WARNING('No FSM models found in app(s): {}'.format(', '.join(app_labels))))
            return

        self.stdout.write('Building FSM documentation for {} model(s)...'.format(len(models)))
        fsm_entries = []
        for model in models:
            try:
                doc = document_fsm_enriched(model)
                fsm_entries.append((model, doc))
                self.stdout.write('  {:<40} lifecycle edges {:>3} -> {:>3}'.format(
                    model._meta.label,
                    docs_graphs.edge_count(doc, collapsed=False),
                    docs_graphs.edge_count(doc, collapsed=True),
                ))
            except Exception as e:
                self.stdout.write(self.style.WARNING('  Skip {}: {}'.format(model._meta.label, e)))

        if not fsm_entries:
            self.stdout.write(self.style.ERROR('No documentation generated.'))
            return

        viz_script = load_viz_script() if options.get('offline') else None
        html = render_html(fsm_entries, viz_script=viz_script)
        out_path = options['output']
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        apps_included = sorted(set(m._meta.app_label for m, _ in fsm_entries))
        self.stdout.write(self.style.SUCCESS(
            'Wrote {} ({} models from apps: {})'.format(
                out_path, len(fsm_entries), ', '.join(apps_included))
        ))
