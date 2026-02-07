"""
Generate clickable HTML documentation for finite state machines.
Documents states, transitions, triggers (with conditions and effects), and periodic tasks.
Runs without database: uses class introspection only.
"""
import re
from django.core.management.base import BaseCommand
from django.utils.html import escape

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
    return {
        'message_class': getattr(message_cls, '__name__', str(message_cls)),
        'subject': getattr(message_cls, 'subject', ''),
        'template': template_path,
        'message_doc': get_doc(message_cls),
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


def _slug_id(name):
    """Slug for state/transition anchor (lowercase, spaces to dashes)."""
    return (name or '').lower().replace(' ', '-')


def _link_to_state(base_id, state_name):
    """Return HTML link to state section."""
    if not base_id or not state_name:
        return escape(str(state_name or ''))
    slug = _slug_id(state_name)
    return '<a href="#{}-state-{}" class="state-link-inline">{}</a>'.format(
        base_id, slug, escape(str(state_name))
    )


def _link_to_transition(base_id, trans_name):
    """Return HTML link to transition section."""
    if not base_id or not trans_name:
        return escape(str(trans_name or ''))
    slug = _slug_id(trans_name)
    return '<a href="#{}-trans-{}" class="transition-link-inline">{}</a>'.format(
        base_id, slug, escape(str(trans_name))
    )


def _render_effect_html(e, base_id=None):
    """Render a single effect (dict with summary/detail or legacy string) to HTML."""
    if isinstance(e, dict):
        summary = escape(str(e.get('summary', '')))
        detail = e.get('detail')
        if not detail:
            return '<li>{}</li>'.format(summary)
        parts = ['<li>', summary]
        doc_str = detail.get('doc')
        if doc_str and not _is_redundant_effect_doc(doc_str, detail):
            parts.append('<p class="effect-doc"><em>{}</em></p>'.format(escape(str(doc_str))))
        notif = detail.get('notification')
        if notif:
            parts.append('<p class="effect-notification">')
            parts.append('<strong>Notification:</strong> {}'.format(escape(notif.get('message_class', ''))))
            if notif.get('subject'):
                parts.append(' &middot; subject: <code>{}</code>'.format(escape(str(notif['subject']))))
            recipients_doc = notif.get('recipients_doc')
            if recipients_doc:
                parts.append('<br><strong>Recipients:</strong> {}'.format(escape(str(recipients_doc))))
            msg_doc = notif.get('message_doc')
            if msg_doc and '(documentation missing)' not in str(msg_doc):
                parts.append('<br><em>{}</em>'.format(escape(str(msg_doc))))
            parts.append('</p>')
            if notif.get('template_rendered'):
                parts.append(
                    '<div class="effect-template-preview">'
                    '<strong>Template preview:</strong>'
                    '<div class="effect-template-body">'
                )
                parts.append(notif['template_rendered'])
                parts.append('</div></div>')
        transition = detail.get('transition')
        if transition:
            parts.append('<p class="effect-related">')
            parts.append('<strong>Transition:</strong> ')
            if transition.get('sources'):
                src_links = ' | '.join(
                    _link_to_state(base_id, s) for s in transition['sources']
                )
                tgt_link = _link_to_state(base_id, transition.get('target', ''))
                parts.append('{} → {} '.format(src_links, tgt_link))
            else:
                tgt_link = _link_to_state(base_id, transition.get('target', ''))
                parts.append('→ {} '.format(tgt_link))
            trans_link = _link_to_transition(
                base_id, transition.get('transition_name', '')
            )
            parts.append('via <em>{}</em>'.format(trans_link))
            parts.append('</p>')
        related = detail.get('related')
        if related:
            parts.append('<p class="effect-related">')
            rel_code = escape(related.get('relation', ''))
            parts.append(
                '<strong>Related transition:</strong> relation <code>{}</code> '.format(rel_code)
            )
            if related.get('sources'):
                rel_src_links = ' | '.join(
                    _link_to_state(base_id, s) for s in related['sources']
                )
                rel_tgt_link = _link_to_state(base_id, related.get('target', ''))
                parts.append('({} → {}) '.format(rel_src_links, rel_tgt_link))
            else:
                rel_tgt_link = _link_to_state(base_id, related.get('target', ''))
                parts.append('→ {} '.format(rel_tgt_link))
            rel_trans_link = _link_to_transition(
                base_id, related.get('transition_name', '')
            )
            parts.append('via transition <em>{}</em>'.format(rel_trans_link))
            parts.append('</p>')
        parts.append('</li>')
        return ''.join(parts)
    return '<li>{}</li>'.format(escape(str(e)))


def get_state_id(state):
    """Id for a state (value or name)."""
    v = getattr(state, 'value', None) or getattr(state, 'name', '')
    return (v if v else 'empty').replace(' ', '-')


def get_transition_id(transition):
    """Id for a transition (field name)."""
    return getattr(transition, 'field', str(transition.name)).replace(' ', '-')


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
    for transition in transitions:
        triggers_for_trans = [
            t for t in model.triggers.triggers
            if isinstance(t, TransitionTrigger) and t.transition == transition
        ]
        effects = []
        for t in triggers_for_trans:
            for effect_cls in t.effects:
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
                    if not any([detail['doc'], detail['notification'], detail['transition'], detail['related']]):
                        detail = None
                    effects.append({'summary': summary, 'detail': detail})
                except Exception:
                    effects.append({'summary': getattr(effect_cls, '__name__', str(effect_cls)), 'detail': None})
        doc['transitions'].append({
            'name': transition.name,
            'description': transition.description or '',
            'from': [s.name.capitalize() for s in transition.sources],
            'to': transition.target.name.capitalize(),
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
        effect_list = []
        for effect_cls in trigger.effects:
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
                if not any([detail['doc'], detail['notification'], detail['transition'], detail['related']]):
                    detail = None
                effect_list.append({'summary': summary, 'detail': detail})
            except Exception:
                effect_list.append({'summary': getattr(effect_cls, '__name__', str(effect_cls)), 'detail': None})
        doc['triggers'].append({
            'when': str(trigger),
            'effects': effect_list,
            'id': re.sub(r'[^a-z0-9]+', '-', str(trigger).lower().strip()).strip('-'),
        })
    # Periodic tasks (model.periodic_tasks)
    for task_cls in getattr(model, 'periodic_tasks', []) or []:
        task_name = getattr(task_cls, '__name__', str(task_cls))
        task_doc = get_doc(task_cls)
        if task_doc and '(documentation missing)' in str(task_doc):
            task_doc = None
        effects = []
        for effect_cls in getattr(task_cls, 'effects', []) or []:
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
                if not any([detail['doc'], detail['notification'], detail['transition'], detail['related']]):
                    detail = None
                effects.append({'summary': summary, 'detail': detail})
            except Exception:
                effects.append({'summary': getattr(effect_cls, '__name__', str(effect_cls)), 'detail': None})
        doc['periodic_tasks'].append({
            'name': task_name,
            'description': task_doc,
            'effects': effects,
        })
    return doc


def document_fsm_enriched(model):
    """
    Like document_model but with state/transition ids and
    for each transition: list of other triggers that can cause it (e.g. model field change).
    Uses class-only introspection so no DB is required.
    """
    return document_fsm_from_classes(model)


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


def render_fsm_section(model_name, model_label, doc, base_id):
    """Render one FSM section (states, transitions, triggers) as HTML."""
    sections = []

    # Build state -> transitions from/to for walk-through
    trans_by_source = {}
    trans_by_target = {}
    for t in doc['transitions']:
        trans_id = '{}-trans-{}'.format(base_id, t.get('id', ''))
        for from_s in t.get('from', []):
            trans_by_source.setdefault(from_s, []).append((t.get('name', ''), trans_id))
        trans_by_target.setdefault(t.get('to', ''), []).append((t.get('name', ''), trans_id))

    # States
    sections.append('<section class="fsm-section states-section" id="{}">'.format(base_id))
    sections.append('<h2>States</h2>')
    sections.append('<ul class="state-list">')
    for s in doc['states']:
        sid = '{}-state-{}'.format(base_id, s.get('id', s.get('name', '').lower().replace(' ', '-')))
        sname = str(s.get('name', ''))
        from_links = trans_by_source.get(sname, [])
        to_links = trans_by_target.get(sname, [])
        sections.append(
            '<li class="state-item" id="{}">'
            '<a href="#{}" class="state-link">'
            '<span class="state-name">{}</span></a>'
            '<p class="state-desc">{}</p>'.format(
                sid, sid,
                escape(sname),
                escape(str(s.get('description', '')))
            )
        )
        if from_links or to_links:
            sections.append('<p class="state-trans">')
            if from_links:
                sections.append('From here: ')
                sections.append(', '.join(
                    '<a href="#{}">{}</a>'.format(tid, escape(tname)) for tname, tid in from_links
                ))
            if from_links and to_links:
                sections.append(' &middot; ')
            if to_links:
                sections.append('To here: ')
                sections.append(', '.join(
                    '<a href="#{}">{}</a>'.format(tid, escape(tname)) for tname, tid in to_links
                ))
            sections.append('</p>')
        sections.append('</li>')
    sections.append('</ul></section>')

    # Transitions
    sections.append('<section class="fsm-section transitions-section" id="{}-transitions">'.format(base_id))
    sections.append('<h2>Transitions</h2>')
    sections.append('<p class="help">Click a transition to see triggers, conditions and effects.</p>')
    sections.append('<ul class="transition-list">')
    for t in doc['transitions']:
        tid = '{}-trans-{}'.format(base_id, t.get('id', ''))
        from_states = t.get('from', [])
        to_state = t.get('to', '')
        manual = t.get('manual', '')
        # Note: state names not linked here to avoid nested <a> (row is a link)
        sections.append(
            '<li class="transition-item" id="{}">'
            '<a href="#{}" class="transition-link">'
            '<span class="trans-name">{}</span> '
            '<span class="trans-arrow">{} → {}</span> '
            '<span class="trans-type">{}</span></a>'.format(
                tid, tid,
                escape(str(t.get('name', ''))),
                escape(' | '.join(from_states) if from_states else '(new)'),
                escape(str(to_state)),
                manual
            )
        )
        # Detail block (hidden by default, shown on click or anchor)
        sections.append('<div class="transition-detail" id="{}-detail">'.format(tid))
        sections.append('<p class="trans-description">{}</p>'.format(escape(str(t.get('description', '')))))
        if t.get('conditions'):
            sections.append('<p><strong>Conditions:</strong></p><ul>')
            for c in t['conditions']:
                sections.append('<li>{}</li>'.format(escape(str(c))))
            sections.append('</ul>')
        if t.get('permission_doc'):
            sections.append('<p><strong>Permission:</strong> {}</p>'.format(escape(t['permission_doc'])))
        sections.append('<p><strong>When this transition runs, effects:</strong></p><ul>')
        for e in t.get('effects', []):
            sections.append(_render_effect_html(e, base_id=base_id))
        sections.append('</ul>')
        caused = t.get('caused_by', [])
        if caused:
            sections.append('<p><strong>Also triggered by:</strong></p><ul>')
            for cb in caused:
                sections.append(
                    '<li>{}'.format(escape(cb['trigger']))
                )
                if cb.get('conditions'):
                    sections.append(' <em>if {}</em>'.format(escape(' and '.join(cb['conditions']))))
                sections.append('</li>')
            sections.append('</ul>')
        sections.append('</div>')
        sections.append('</li>')
    sections.append('</ul></section>')

    # Other triggers (e.g. model field changed)
    if doc.get('triggers'):
        sections.append('<section class="fsm-section other-triggers-section" id="{}-triggers">'.format(base_id))
        sections.append('<h2>Other triggers (e.g. field changes)</h2>')
        sections.append('<ul class="trigger-list">')
        for tr in doc['triggers']:
            trid = '{}-trigger-{}'.format(base_id, tr.get('id', ''))
            sections.append(
                '<li class="trigger-item" id="{}">'
                '<strong>{}</strong>'.format(trid, escape(tr['when']))
            )
            sections.append('<ul>')
            for e in tr.get('effects', []):
                sections.append(_render_effect_html(e, base_id=base_id))
            sections.append('</ul></li>')
        sections.append('</ul></section>')

    # Periodic tasks
    if doc.get('periodic_tasks'):
        sections.append('<section class="fsm-section periodic-tasks-section" id="{}-periodic-tasks">'.format(base_id))
        sections.append('<h2>Periodic tasks</h2>')
        sections.append(
            '<p class="help">Scheduled tasks that run (e.g. via cron) and apply '
            'effects to matching instances.</p>'
        )
        sections.append('<ul class="trigger-list">')
        for pt in doc['periodic_tasks']:
            pt_id = '{}-periodic-{}'.format(base_id, re.sub(r'[^a-z0-9]+', '-', pt.get('name', '').lower()))
            sections.append('<li class="trigger-item" id="{}">'.format(pt_id))
            sections.append('<strong>{}</strong>'.format(escape(pt.get('name', ''))))
            if pt.get('description'):
                sections.append('<p class="task-description">{}</p>'.format(escape(str(pt['description']))))
            sections.append('<ul>')
            for e in pt.get('effects', []):
                sections.append(_render_effect_html(e, base_id=base_id))
            sections.append('</ul></li>')
        sections.append('</ul></section>')

    return '\n'.join(sections)


def render_html(fsm_entries):
    """
    Full HTML page with nav and FSM sections. Styling matches preview_all_messages.
    fsm_entries: list of (model_class, doc_dict) where doc_dict is from document_fsm_enriched.
    """
    # Build nav links from entries, grouped by app; and "Jump to app" links
    from collections import OrderedDict
    by_app = OrderedDict()
    first_id_by_app = {}
    for model, doc in fsm_entries:
        app = model._meta.app_label
        if app not in by_app:
            by_app[app] = []
            first_id_by_app[app] = model._meta.model_name
        base_id = model._meta.model_name
        label = model._meta.verbose_name
        by_app[app].append('<li><a href="#{}">{}</a></li>'.format(base_id, escape(label)))
    nav_items = []
    for app_label, links in by_app.items():
        app_display = app_label.replace('_', ' ').title()
        nav_items.append('<li class="nav-app-group"><strong>{}</strong></li>'.format(escape(app_display)))
        for link in links:
            nav_items.append(link)
    nav_html = '\n    '.join(nav_items)
    jump_links = ' | '.join(
        '<a href="#{}">{}</a>'.format(first_id_by_app[app], escape(app.replace('_', ' ').title()))
        for app in first_id_by_app
    )
    apps_label = ', '.join(sorted(set(e[0]._meta.app_label for e in fsm_entries)))
    title = 'FSM documentation – ' + apps_label

    html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 40px 20px;
  line-height: 1.5;
  color: #333;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
header {{
  text-align: center;
  color: white;
  margin-bottom: 40px;
}}
header h1 {{ font-size: 48px; margin-bottom: 10px; }}
header p {{ font-size: 18px; opacity: 0.95; }}
header p.jump-to {{ font-size: 16px; margin-top: 12px; }}
header p.jump-to a {{ color: white; text-decoration: underline; font-weight: 600; }}
header p.jump-to a:hover {{ opacity: 0.9; }}
nav {{
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 30px;
}}
nav ul {{ list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; }}
nav ul {{ gap: 0.5rem 1rem; align-items: center; }}
nav li {{ margin: 0; }}
nav li.nav-app-group {{ width: 100%; margin: 0.5rem 0 0.15rem; font-size: 0.85rem; opacity: 0.95; }}
nav li.nav-app-group:first-child {{ margin-top: 0; }}
nav a {{ color: white; text-decoration: none; font-weight: 500; }}
nav a:hover {{ text-decoration: underline; }}
.fsm-block {{
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}}
.fsm-block-sticky-header {{
  position: sticky;
  top: 0;
  z-index: 100;
  padding-top: 0.5rem;
  padding-bottom: 1rem;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
  background: white;
  border-radius: 12px 12px 0 0;
}}
.fsm-block-sticky-header.is-stuck {{
  width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  padding-left: calc(50vw - 50% + 30px);
  padding-right: calc(50vw - 50% + 30px);
  border-radius: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}
.fsm-block-header {{
  display: flex;
  align-items: flex-start;
}}
.fsm-block h1 {{
  color: #667eea;
  margin-bottom: 0;
  font-size: 28px;
  min-width: 0;
}}
.back-to-top-fixed {{
  position: fixed;
  top: 1rem;
  right: 1.5rem;
  z-index: 1000;
  background: #667eea;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}}
.back-to-top-fixed:hover {{
  background: #5a6fd6;
  color: white;
  text-decoration: none;
}}
.fsm-class-path {{
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 16px;
  font-family: ui-monospace, monospace;
}}
.fsm-class-path code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.8rem; }}
.fsm-section {{ margin-bottom: 28px; }}
.fsm-section h2 {{
  color: #667eea;
  border-bottom: 2px solid #667eea;
  padding-bottom: 8px;
  margin-bottom: 15px;
  font-size: 20px;
}}
.help {{ color: #666; font-size: 0.9rem; margin-bottom: 1rem; }}
.model-description {{ color: #666; font-size: 0.9rem; margin-bottom: 1rem; }}
.task-description {{ color: #666; font-size: 0.9rem; margin: 0.35rem 0 0; }}
.state-list, .transition-list, .trigger-list {{ list-style: none; padding: 0; }}
.state-item, .transition-item, .trigger-item {{
  background: #f5f5f5;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
  border-left: 4px solid #667eea;
}}
.state-link, .transition-link {{ font-weight: 600; color: #333; text-decoration: none; }}
.state-link:hover, .transition-link:hover {{ color: #667eea; text-decoration: underline; }}
.state-desc, .trans-description {{ color: #666; font-size: 0.9rem; margin: 0.35rem 0 0; }}
.state-trans {{ font-size: 0.85rem; margin: 0.35rem 0 0; color: #666; }}
.state-trans a {{ color: #667eea; margin-right: 0.25rem; }}
.state-link-inline, .transition-link-inline {{ color: #667eea; text-decoration: none; }}
.state-link-inline:hover, .transition-link-inline:hover {{ text-decoration: underline; }}
.trans-arrow {{ color: #28a745; }}
.trans-type {{ font-size: 0.85rem; color: #fd7e14; margin-left: 0.5rem; }}
.transition-detail {{
  display: none;
  margin-top: 12px;
  padding: 15px;
  background: #f8f9fa;
  border-left: 4px solid #667eea;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #495057;
}}
.transition-detail ul {{ margin: 0.35rem 0; padding-left: 1.25rem; }}
.transition-detail strong {{ color: #667eea; }}
.effect-doc, .effect-notification, .effect-related {{
  margin: 0.35rem 0;
  font-size: 0.85rem;
  color: #666;
  padding: 8px;
  background: #fff8e1;
  border-left: 3px solid #ffc107;
  border-radius: 3px;
}}
.effect-notification code, .effect-related code {{
  font-size: 0.8rem; background: #e9ecef; padding: 2px 5px; border-radius: 3px;
}}
.effect-template-preview {{
  margin-top: 0.5rem;
  font-size: 0.85rem;
}}
.effect-template-preview strong {{
  display: block;
  margin-bottom: 0.35rem;
  color: #495057;
}}
.effect-template-body {{
  max-height: 200px;
  overflow: auto;
  padding: 0.75rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.8rem;
}}
.effect-template-body p {{ margin: 0.35rem 0; }}
@media (max-width: 768px) {{
  header h1 {{ font-size: 32px; }}
  .fsm-block {{ padding: 20px; }}
}}
</style>
</head>
<body>
<div class="container" id="top">
<header>
  <h1>📊 FSM Documentation</h1>
  <p>{apps_label} – states, transitions, triggers and effects</p>
  <p class="jump-to">Jump to: {jump_links}</p>
</header>
<nav>
  <ul>
    {nav_html}
  </ul>
</nav>
'''.format(title=escape(title), apps_label=escape(apps_label), jump_links=jump_links, nav_html=nav_html)

    for model, doc in fsm_entries:
        base_id = model._meta.model_name
        label = model._meta.verbose_name
        class_path = '{}.{}'.format(model.__module__, model.__name__)
        html += (
            '<div class="fsm-block" id="{}">\n'
            '  <div class="fsm-block-sticky-header">\n'
            '    <div class="fsm-block-header">\n'
            '      <h1>{}</h1>\n'
            '    </div>\n'
            '  </div>\n'
            '  <p class="fsm-class-path"><code>{}</code></p>\n'
        ).format(base_id, escape(label), escape(class_path))
        model_doc = getattr(model, '__doc__', None)
        if model_doc and isinstance(model_doc, str) and model_doc.strip():
            html += '<p class="model-description">{}</p>\n'.format(
                escape(re.sub(r'\s+', ' ', model_doc.strip()))
            )
        html += render_fsm_section(label, label, doc, base_id)
        html += '\n</div>\n'

    html += '''
</div>
<a href="#top" class="back-to-top-fixed" aria-label="Back to top">Back to top</a>
<script>
(function(){
  function openDetail(id) {
    var detail = document.getElementById(id + '-detail');
    if (detail) {
      document.querySelectorAll('.transition-detail').forEach(function(d){ d.style.display = 'none'; });
      detail.style.display = 'block';
      document.getElementById(id).scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
  function onHashChange() {
    var hash = window.location.hash.slice(1);
    if (hash && hash.endsWith('-detail')) hash = hash.slice(0, -7);
    if (hash) openDetail(hash);
  }
  if (window.location.hash) onHashChange();
  window.addEventListener('hashchange', onHashChange);
  document.querySelectorAll('.transition-link').forEach(function(a){
    a.addEventListener('click', function(e){
      var id = this.getAttribute('href').slice(1);
      var detail = document.getElementById(id + '-detail');
      if (detail) {
        var open = detail.style.display === 'block';
        document.querySelectorAll('.transition-detail').forEach(function(d){ d.style.display = 'none'; });
        if (!open) { detail.style.display = 'block'; window.location.hash = id; }
      }
    });
  });
  function updateStickyHeaders() {
    document.querySelectorAll('.fsm-block-sticky-header').forEach(function(header) {
      var rect = header.getBoundingClientRect();
      if (rect.top <= 2) {
        header.classList.add('is-stuck');
      } else {
        header.classList.remove('is-stuck');
      }
    });
  }
  var scrollTicking = false;
  window.addEventListener('scroll', function() {
    if (!scrollTicking) {
      window.requestAnimationFrame(function() {
        updateStickyHeaders();
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  }, { passive: true });
  updateStickyHeaders();
})();
</script>
</body>
</html>
'''
    return html


class Command(BaseCommand):
    help = (
        'Generate clickable HTML documentation for FSM models (states, transitions, '
        'triggers, conditions, effects). By default includes deeds, funding, funding_stripe, '
        'collect, grant_management, time_based, initiatives. Use --app to limit to specific app(s). No DB required.'
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
                self.stdout.write('  {}'.format(model._meta.label))
            except Exception as e:
                self.stdout.write(self.style.WARNING('  Skip {}: {}'.format(model._meta.label, e)))

        if not fsm_entries:
            self.stdout.write(self.style.ERROR('No documentation generated.'))
            return

        html = render_html(fsm_entries)
        out_path = options['output']
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        apps_included = sorted(set(m._meta.app_label for m, _ in fsm_entries))
        self.stdout.write(self.style.SUCCESS(
            'Wrote {} ({} models from apps: {})'.format(
                out_path, len(fsm_entries), ', '.join(apps_included))
        ))
