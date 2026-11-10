"""
Graph builders for the generated FSM documentation.

Every builder returns a plain dict ``{'attrs', 'nodes', 'edges', 'clusters'}``
that :func:`to_dot` turns into Graphviz DOT. The page renders the DOT in the
browser, so nothing here needs Django, the database or a graphviz binary.

The builders keep graphs small on purpose:

* :func:`lifecycle_graph` shows states and transitions only. States are grouped
  into phases (setting up, active, finished, stopped). A transition that leaves
  every state of a phase is drawn once from the phase. Transitions that can
  start from (almost) any state are collapsed into a note on their target
  state, and parallel transitions between the same two states share one edge.
* :func:`effects_graph` shows one transition and its direct effects.
* :func:`cascade_graph` follows related transitions across models.
* :func:`family_map` shows which models can change the state of which others.
"""
import math
from html import escape

GLOBAL_MIN_SOURCES = 4
GLOBAL_RATIO = 0.6
CASCADE_DEPTH = 3
MAX_LABEL = 48

INITIAL = 'empty'
ALL = 'all'

PHASES = [
    ('setup', 'Setting up', [
        'draft', 'needs_work', 'submitted', 'new', 'pending', 'planned', 'incomplete', 'unverified',
        'action_needed',
    ]),
    ('active', 'Active', [
        'open', 'full', 'registration_closed', 'running', 'scheduled', 'accepted', 'active', 'approved',
        'started', 'granted', 'verified', 'charged',
    ]),
    ('finished', 'Finished', ['succeeded', 'finished', 'expired', 'failed', 'final']),
    ('stopped', 'Stopped', [
        'cancelled', 'canceled', 'rejected', 'deleted', 'withdrawn', 'removed', 'stopped', 'refunded',
        'refund_requested', 'activity_refunded', 'disputed', 'disabled',
    ]),
]
PHASE_OF = {state: phase for phase, _, states in PHASES for state in states}
MIN_STATES_FOR_PHASES = 6

THEME = {
    'font': 'Helvetica,Arial,sans-serif',
    'state_fill': '#eef4fb',
    'state_border': '#4a6fa5',
    'terminal_fill': '#f4f4f4',
    'manual': '#1f2d3d',
    'automatic': '#8a94a3',
    'note': '#7a5c00',
    'related': '#eaf6ee',
    'notification': '#fff6e0',
    'own': '#eef4fb',
    'other': '#f4f4f4',
    'incoming': '#f3eefb',
    'root': '#1f2d3d',
}


def truncate(text, length=MAX_LABEL):
    text = ' '.join(str(text or '').split())
    if len(text) <= length:
        return text
    return text[:length - 1].rstrip() + '…'


def is_global(transition, state_ids):
    """True when a transition starts from so many states that drawing every edge adds only noise."""
    sources = set(transition['from_ids'])
    if ALL in sources:
        return True
    others = [s for s in state_ids if s not in (INITIAL, transition['to_id'])]
    sources = sources.intersection(others)
    threshold = max(GLOBAL_MIN_SOURCES, math.ceil(GLOBAL_RATIO * len(others)))
    return len(sources) >= threshold


def _graph(**attrs):
    return {'attrs': attrs, 'nodes': [], 'edges': [], 'clusters': []}


def _html_rows(rows, bold_first=False):
    """HTML-like label: one table row per (text, href, muted) tuple."""
    cells = []
    for index, (text, href, muted) in enumerate(rows):
        content = escape(text)
        if bold_first and index == 0:
            content = '<B>{}</B>'.format(content)
        if muted:
            content = '<FONT POINT-SIZE="9" COLOR="{}">{}</FONT>'.format(THEME['note'], content)
        attrs = ' HREF="{}" TITLE="{}"'.format(escape(href), escape(text)) if href else ''
        cells.append('<TR><TD{}>{}</TD></TR>'.format(attrs, content))
    return '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">{}</TABLE>>'.format(''.join(cells))


def get_phases(state_ids):
    """Phase id -> state ids, for phases that hold at least two states; empty for small machines."""
    real = [s for s in state_ids if s != INITIAL]
    if len(real) < MIN_STATES_FOR_PHASES:
        return {}
    phases = {}
    for state_id in real:
        if state_id in PHASE_OF:
            phases.setdefault(PHASE_OF[state_id], []).append(state_id)
    return {phase: states for phase, states in phases.items() if len(states) > 1}


def _phase_tails(transition, phases):
    """Split the sources of a transition into whole phases and the remaining single states."""
    sources = [s for s in transition['from_ids'] if s != ALL]
    tails = []
    for phase, states in phases.items():
        if transition['to_id'] not in states and set(states) <= set(sources):
            tails.append(('phase', phase))
            sources = [s for s in sources if s not in states]
    return tails, sources


def _phase_label(phase):
    return dict((p, label) for p, label, _ in PHASES)[phase]


def lifecycle_graph(doc, base_id, show_automatic=True, expand_global=False):
    """
    States and transitions of one model.

    Sources are drawn as compactly as possible: a whole phase becomes one arrow from
    the phase, and a set of states that several transitions share meets in a junction
    point first, so each source state needs one line instead of one per transition.
    """
    state_ids = [s['id'] for s in doc['states']]
    labels = {s['id']: s['name'] for s in doc['states']}
    state_descriptions = {s['id']: str(s.get('description') or '') for s in doc['states']}
    phases = get_phases(state_ids)
    graph = _graph(rankdir='TB', nodesep='0.4', ranksep='0.45', compound='true', newrank='true')
    graph['globals'] = []

    outgoing = set()
    for transition in doc['transitions']:
        outgoing.update(transition['from_ids'])

    collapsed = {}
    visible = []
    for transition in doc['transitions']:
        automatic = transition['manual'] == 'Automatic'
        if automatic and not show_automatic:
            continue
        url = '#{}-trans-{}'.format(base_id, transition['id'])
        if is_global(transition, state_ids) and not expand_global:
            collapsed.setdefault(transition['to_id'], []).append((transition, url))
            graph['globals'].append({
                'name': transition['name'],
                'url': url,
                'to': labels.get(transition['to_id'], transition['to_id']),
                'sources': len(transition['from_ids']),
                'automatic': automatic,
            })
            continue
        tails, rest = _phase_tails(transition, phases)
        visible.append((transition, url, automatic, tails, rest))

    shared = {}
    for _, _, _, _, rest in visible:
        if len(rest) > 1:
            key = tuple(sorted(rest))
            shared[key] = shared.get(key, 0) + 1
    junctions = {key: 'j{}'.format(i) for i, key in enumerate(k for k, count in shared.items() if count > 1)}

    edges = {}
    referenced = set(collapsed)
    for transition, url, automatic, tails, rest in visible:
        key = tuple(sorted(rest))
        if key in junctions:
            tails = tails + [('junction', junctions[key])]
        else:
            tails = tails + [('state', source) for source in rest]
        for tail in tails:
            edges.setdefault(tail + (transition['to_id'], automatic), []).append((transition, url))
        referenced.update(transition['from_ids'] + [transition['to_id']])

    for state_id in state_ids:
        if state_id == INITIAL:
            if INITIAL in referenced:
                graph['nodes'].append({
                    'id': INITIAL, 'shape': 'point', 'width': '0.18', 'color': THEME['manual'],
                    'tooltip': 'New object',
                })
            continue
        rows = [(labels[state_id], '#{}-state-{}'.format(base_id, state_id), False)]
        for transition, url in collapsed.get(state_id, []):
            rows.append(('⇐ {} (from {} states)'.format(transition['name'], len(transition['from_ids'])), url, True))
        terminal = state_id not in outgoing
        phase = PHASE_OF.get(state_id)
        nodes = graph['nodes']
        if state_id in phases.get(phase, []):
            cluster = next((c for c in graph['clusters'] if c['id'] == phase), None)
            if cluster is None:
                cluster = {'id': phase, 'label': _phase_label(phase), 'fillcolor': '#fafbfd', 'nodes': []}
                graph['clusters'].append(cluster)
            nodes = cluster['nodes']
        nodes.append({
            'id': state_id,
            'html': _html_rows(rows, bold_first=True),
            'shape': 'box',
            'style': 'rounded,filled',
            'peripheries': '2' if terminal else '1',
            'fillcolor': THEME['terminal_fill'] if terminal else THEME['state_fill'],
            'color': THEME['state_border'],
            'tooltip': state_descriptions.get(state_id) or labels[state_id],
            'class': 'n-{}'.format(state_id),
        })

    order = [phase for phase, _, _ in PHASES]
    graph['clusters'].sort(key=lambda cluster: order.index(cluster['id']))
    if 'stopped' in phases:
        graph['ranks'] = [('max', phases['stopped'])]

    junction_targets = {}
    for (kind, tail, target, automatic), transitions in edges.items():
        if kind == 'phase':
            sources = phases[tail]
        elif kind == 'junction':
            sources = next(list(k) for k, j in junctions.items() if j == tail)
            junction_targets.setdefault(tail, []).append(target)
        else:
            sources = [tail]
        edge = {
            'source': tail if kind == 'junction' else sources[0],
            'target': target,
            'html': _html_rows([(t['name'], url, False) for t, url in transitions]),
            'style': 'dashed' if automatic else 'solid',
            'color': THEME['automatic'] if automatic else THEME['manual'],
            'fontcolor': THEME['automatic'] if automatic else THEME['manual'],
            'tooltip': ', '.join(t['name'] for t, _ in transitions),
            'class': ' '.join(['e-from-{}'.format(s) for s in sources] + ['e-to-{}'.format(target)]),
        }
        if kind == 'phase':
            edge['ltail'] = 'cluster_' + tail
            edge['tooltip'] += ' (from every {} state)'.format(_phase_label(tail).lower())
        else:
            edge['tooltip'] += ' (from {})'.format(', '.join(labels.get(s, s) for s in sources))
        graph['edges'].append(edge)

    for key, junction in junctions.items():
        graph['nodes'].append({
            'id': junction, 'shape': 'point', 'width': '0.08', 'color': THEME['automatic'],
            'tooltip': 'From ' + ', '.join(labels.get(s, s) for s in key),
        })
        targets = ['e-to-{}'.format(t) for t in junction_targets.get(junction, [])]
        for source in key:
            graph['edges'].insert(0, {
                'source': source, 'target': junction, 'arrowhead': 'none', 'color': THEME['automatic'],
                'tooltip': 'From ' + ', '.join(labels.get(s, s) for s in key),
                'class': ' '.join(['e-from-{}'.format(source)] + targets),
            })
    return graph


def lifecycle_variants(doc, base_id):
    """Pre-built DOT for each toolbar combination, so the page never has to write DOT itself."""
    return {
        'a{}g{}'.format(int(automatic), int(expand)): to_dot(
            lifecycle_graph(doc, base_id, show_automatic=automatic, expand_global=expand)
        )
        for automatic in (True, False)
        for expand in (True, False)
    }


def edge_count(doc, collapsed=True):
    graph = lifecycle_graph(doc, 'x', expand_global=not collapsed)
    if collapsed:
        return len(graph['edges'])
    return sum(len([s for s in t['from_ids'] if s != ALL]) for t in doc['transitions'])


EFFECT_KINDS = [
    ('own', 'Status changes on this object'),
    ('related', 'Related objects'),
    ('notification', 'Notifications'),
    ('other', 'Other effects'),
]


def effects_graph(transition, base_id):
    """One transition, the triggers that cause it, and its direct effects."""
    effects = []
    seen = set()
    for effect in transition['effects']:
        info = effect.get('graph')
        key = info and (info['kind'], info['label'], info.get('conditions'))
        if info and key not in seen:
            seen.add(key)
            effects.append(effect)
    incoming = transition.get('incoming', [])
    if not effects and not incoming:
        return None

    graph = _graph(rankdir='LR', nodesep='0.15', ranksep='0.5')
    root = 'root'
    graph['nodes'].append({
        'id': root,
        'html': _html_rows([
            (transition['name'], None, False),
            (truncate('{} → {}'.format(' | '.join(transition['from_states']) or 'new', transition['to']), 70),
             None, True),
        ], bold_first=True),
        'shape': 'box', 'style': 'rounded,bold', 'color': THEME['root'],
        'tooltip': transition.get('description') or transition['name'],
    })

    if incoming:
        cluster = {'id': 'incoming', 'label': 'Caused by', 'fillcolor': THEME['incoming'], 'nodes': []}
        for index, source in enumerate(incoming):
            node_id = 'in{}'.format(index)
            cluster['nodes'].append({
                'id': node_id, 'label': truncate(source['label']), 'url': source.get('url'),
                'tooltip': source['label'], 'shape': 'box', 'style': 'rounded',
            })
            graph['edges'].append({
                'source': node_id, 'target': root,
                'label': truncate('if ' + source['conditions'], 32) if source.get('conditions') else '',
                'tooltip': source.get('conditions') or source['label'],
                'color': THEME['automatic'],
            })
        graph['clusters'].append(cluster)

    for kind, label in EFFECT_KINDS:
        cluster = {'id': kind, 'label': label, 'fillcolor': THEME[kind], 'nodes': []}
        for index, effect in enumerate(e for e in effects if e['graph']['kind'] == kind):
            node_id = '{}{}'.format(kind, index)
            info = effect['graph']
            cluster['nodes'].append({
                'id': node_id,
                'label': truncate(info['label'], 56),
                'url': info.get('url'),
                'tooltip': info.get('tooltip') or info['label'],
                'shape': 'note' if kind == 'notification' else 'box',
                'style': 'filled' if kind == 'notification' else 'rounded',
                'fillcolor': THEME['notification'],
            })
            conditions = info.get('conditions')
            graph['edges'].append({
                'source': root, 'target': node_id,
                'label': truncate('if ' + conditions, 32) if conditions else '',
                'tooltip': 'if ' + conditions if conditions else info['label'],
            })
        if cluster['nodes']:
            graph['clusters'].append(cluster)
    return graph


def cascade_graph(index, start, depth=CASCADE_DEPTH):
    """
    Follow related transitions from ``start`` (a ``(base_id, transition_id)`` key).

    ``index`` maps keys to ``{'model', 'name', 'url', 'notifications', 'related': [...]}``
    where each related entry is ``{'relation', 'conditions', 'targets': [keys]}``.
    Each key is drawn once, so cycles end where they loop back.
    """
    if start not in index or not index[start]['related']:
        return None
    graph = _graph(rankdir='LR', nodesep='0.2', ranksep='0.6', compound='true')
    clusters = {}
    seen = {}
    edges = set()

    def add_node(key, level):
        entry = index[key]
        node_id = 'c{}'.format(len(seen))
        seen[key] = node_id
        label = entry['name']
        if entry['notifications']:
            label += '  ✉{}'.format(entry['notifications'])
        cluster = clusters.setdefault(entry['model'], {
            'id': 'm{}'.format(len(clusters)), 'label': entry['model'],
            'fillcolor': THEME['state_fill'], 'nodes': [],
        })
        cluster['nodes'].append({
            'id': node_id, 'label': label, 'url': entry['url'], 'shape': 'box',
            'style': 'rounded,bold' if level == 0 else 'rounded,filled', 'fillcolor': 'white',
            'tooltip': '{}: {}'.format(entry['model'], entry['name']),
        })
        return node_id

    queue = [(start, 0)]
    add_node(start, 0)
    truncated = 0
    while queue:
        key, level = queue.pop(0)
        for related in index[key]['related']:
            for target in related['targets']:
                if target not in index:
                    continue
                if target not in seen:
                    if level + 1 > depth:
                        truncated += 1
                        continue
                    add_node(target, level + 1)
                    queue.append((target, level + 1))
                edge = (seen[key], seen[target], related['relation'])
                if edge in edges:
                    continue
                edges.add(edge)
                conditions = related.get('conditions')
                graph['edges'].append({
                    'source': seen[key], 'target': seen[target],
                    'label': related['relation'] + (' *' if conditions else ''),
                    'tooltip': 'if ' + conditions if conditions else related['relation'],
                    'style': 'dashed' if conditions else 'solid',
                })
    graph['clusters'] = list(clusters.values())
    graph['truncated'] = truncated
    return graph


def family_map(models, index):
    """Models of one family, with an edge when a transition on one can change the state of another."""
    labels = dict(models)
    counts = {}
    for (base_id, _), entry in index.items():
        if base_id not in labels:
            continue
        for related in entry['related']:
            for target_base, _ in related['targets']:
                if target_base in labels and target_base != base_id:
                    counts[(base_id, target_base)] = counts.get((base_id, target_base), 0) + 1
    if not counts:
        return None
    graph = _graph(rankdir='LR', nodesep='0.3', ranksep='0.8')
    for base_id, label in models:
        graph['nodes'].append({
            'id': base_id, 'label': label, 'url': '#' + base_id, 'shape': 'box',
            'style': 'rounded,filled', 'fillcolor': THEME['state_fill'], 'color': THEME['state_border'],
        })
    for (source, target), count in sorted(counts.items()):
        graph['edges'].append({
            'source': source, 'target': target, 'label': str(count),
            'tooltip': '{} transition effect(s) on {}'.format(count, labels[target]),
            'penwidth': str(min(1 + count / 4, 4)),
        })
    return graph


def _quote(value):
    return '"{}"'.format(str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n'))


NODE_KEYS = ['shape', 'style', 'fillcolor', 'color', 'peripheries', 'width', 'tooltip', 'class']
EDGE_KEYS = ['style', 'color', 'fontcolor', 'tooltip', 'class', 'penwidth', 'ltail', 'arrowhead']


def _attrs(item, keys):
    parts = []
    if item.get('html'):
        parts.append('label={}'.format(item['html']))
    elif 'label' in item:
        parts.append('label={}'.format(_quote(item['label'])))
    if item.get('url'):
        parts.append('URL={}'.format(_quote(item['url'])))
        parts.append('target="_self"')
    for key in keys:
        if item.get(key):
            parts.append('{}={}'.format(key, _quote(item[key])))
    return ' [{}]'.format(', '.join(parts)) if parts else ''


def _node_line(node, indent):
    return '{}{}{};'.format(indent, _quote(node['id']), _attrs(node, NODE_KEYS))


def to_dot(graph):
    lines = ['digraph G {']
    attrs = dict(graph['attrs'])
    attrs.setdefault('bgcolor', 'transparent')
    attrs.setdefault('fontname', THEME['font'])
    for key, value in attrs.items():
        lines.append('  {}={};'.format(key, _quote(value)))
    lines.append('  node [fontname={0}, fontsize="11", margin="0.12,0.04"];'.format(_quote(THEME['font'])))
    lines.append('  edge [fontname={0}, fontsize="10", arrowsize="0.7"];'.format(_quote(THEME['font'])))
    for node in graph['nodes']:
        lines.append(_node_line(node, '  '))
    for cluster in graph['clusters']:
        lines.append('  subgraph {} {{'.format(_quote('cluster_' + cluster['id'])))
        lines.append('    label={}; style="rounded,filled"; color="#d0d7e2"; fillcolor={}; '
                     'fontsize="10"; labeljust="l";'.format(_quote(cluster['label']), _quote(cluster['fillcolor'])))
        for node in cluster['nodes']:
            lines.append(_node_line(node, '    '))
        lines.append('  }')
    for rank, members in graph.get('ranks', []):
        lines.append('  {{rank={}; {}}}'.format(rank, ' '.join(_quote(m) for m in members)))
    for edge in graph['edges']:
        lines.append('  {} -> {}{};'.format(_quote(edge['source']), _quote(edge['target']), _attrs(edge, EDGE_KEYS)))
    lines.append('}')
    return '\n'.join(lines)
