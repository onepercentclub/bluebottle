"""
Generate clickable HTML documentation for finite state machines.

Responsibilities are split as follows:

- Introspection helpers in this module build a plain Python ``doc`` structure
  describing states, transitions, triggers and periodic tasks for each model.
- ``render_html`` turns that structure into a template context and renders a
  Django template (HTML lives in ``templates/fsm/fsm_documentation.html``).
- Styling is served from a static CSS file
  (``static/fsm/fsm_documentation.css``).

This command does not require database queries for state-machine inspection;
it uses class introspection only.
"""
import re
from collections import OrderedDict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

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
                    else:
                        detail['show_doc'] = not _is_redundant_effect_doc(detail.get('doc'), detail)
                    effects.append({'summary': summary, 'detail': detail})
                except Exception:
                    effects.append({'summary': getattr(effect_cls, '__name__', str(effect_cls)), 'detail': None})
        doc['transitions'].append({
            'name': transition.name,
            'description': transition.description or '',
            'from_states': [s.name.capitalize() for s in transition.sources],
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
                else:
                    detail['show_doc'] = not _is_redundant_effect_doc(detail.get('doc'), detail)
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
                else:
                    detail['show_doc'] = not _is_redundant_effect_doc(detail.get('doc'), detail)
                effects.append({'summary': summary, 'detail': detail})
            except Exception:
                effects.append({'summary': getattr(effect_cls, '__name__', str(effect_cls)), 'detail': None})
        doc['periodic_tasks'].append({
            'name': task_name,
            'id': re.sub(r'[^a-z0-9]+', '-', task_name.lower()).strip('-') or 'task',
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


def render_html(fsm_entries):
    """
    Render the FSM documentation page using a Django template.

    ``fsm_entries`` is a list of ``(model_class, doc_dict)`` where
    ``doc_dict`` comes from :func:`document_fsm_enriched`.
    """
    if not fsm_entries:
        return ''

    # Build grouped navigation data by app; keep order stable.
    by_app: OrderedDict[str, list] = OrderedDict()
    first_id_by_app: dict[str, str] = {}
    sections = []

    for model, doc in fsm_entries:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        verbose_name = model._meta.verbose_name

        if app_label not in by_app:
            by_app[app_label] = []
            first_id_by_app[app_label] = model_name

        by_app[app_label].append(
            {
                'id': model_name,
                'label': verbose_name,
            }
        )

        class_path = f'{model.__module__}.{model.__name__}'
        model_doc = getattr(model, '__doc__', None)
        if model_doc and isinstance(model_doc, str) and model_doc.strip():
            model_doc = re.sub(r'\s+', ' ', model_doc.strip())
        else:
            model_doc = ''

        sections.append(
            {
                'base_id': model_name,
                'label': verbose_name,
                'class_path': class_path,
                'model_doc': model_doc,
                'doc': doc,
                'state_links': _state_links_from_doc(doc, model_name),
            }
        )

    # Build nav groups for the template
    nav_groups = []
    for app_label, models in by_app.items():
        nav_groups.append(
            {
                'app_label': app_label.replace('_', ' ').title(),
                'models': models,
            }
        )

    jump_links = [
        {'href': '#{}'.format(first_id_by_app[app]), 'label': app.replace('_', ' ').title()}
        for app in first_id_by_app
    ]
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
        'nav_groups': nav_groups,
        'jump_links': jump_links,
        'sections': sections,
        'inline_css': inline_css,
    }

    return render_to_string('fsm/fsm_documentation.html', context)


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
