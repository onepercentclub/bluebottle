import os
import shutil
import subprocess
import tempfile

from django.core.management import call_command
from django.test import SimpleTestCase

from bluebottle.fsm import docs_graphs
from bluebottle.fsm.management.commands.generate_fsm_docs import (
    build_graph_index, document_fsm_enriched, get_fsm_models_for_apps
)
from bluebottle.test.utils import BluebottleTestCase


def state(state_id):
    return {'id': state_id, 'name': state_id.capitalize()}


def transition(name, sources, target, automatic=False):
    return {
        'id': name, 'name': name.capitalize(), 'from_ids': sources, 'to_id': target,
        'from_states': [s.capitalize() for s in sources], 'to': target.capitalize(),
        'manual': 'Automatic' if automatic else 'Manual', 'effects': [],
    }


def edges_named(graph, name):
    return [e for e in graph['edges'] if name.capitalize() in e.get('tooltip', '').split(' (')[0].split(', ')]


class LifecycleGraphTestCase(SimpleTestCase):
    def setUp(self):
        self.doc = {
            'states': [state(s) for s in ['empty', 'new', 'open', 'full', 'succeeded', 'cancelled']],
            'transitions': [
                transition('initiate', ['empty'], 'new', automatic=True),
                transition('approve', ['new'], 'open'),
                transition('publish', ['new'], 'open'),
                transition('lock', ['open'], 'full', automatic=True),
                transition('cancel', ['new', 'open', 'full', 'succeeded'], 'cancelled'),
            ],
        }

    def test_transition_from_most_states_is_collapsed(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model')

        self.assertEqual(edges_named(graph, 'cancel'), [])
        self.assertEqual([g['name'] for g in graph['globals']], ['Cancel'])
        cancelled = next(n for n in graph['nodes'] if n['id'] == 'cancelled')
        self.assertIn('Cancel (from 4 states)', cancelled['html'])

    def test_expand_global(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model', expand_global=True)

        self.assertEqual(graph['globals'], [])
        self.assertEqual(len(edges_named(graph, 'cancel')), 4)

    def test_parallel_transitions_share_an_edge(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model')

        edges = [e for e in graph['edges'] if (e['source'], e['target']) == ('new', 'open')]
        self.assertEqual(len(edges), 1)
        self.assertIn('#model-trans-approve', edges[0]['html'])
        self.assertIn('#model-trans-publish', edges[0]['html'])

    def test_hide_automatic(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model', show_automatic=False)

        self.assertEqual(edges_named(graph, 'lock'), [])
        self.assertFalse(any(n['id'] == 'empty' for n in graph['nodes']))
        self.assertEqual(len(edges_named(graph, 'approve')), 1)

    def test_automatic_edges_are_dashed(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model')

        self.assertEqual(edges_named(graph, 'lock')[0]['style'], 'dashed')
        self.assertEqual(edges_named(graph, 'approve')[0]['style'], 'solid')

    def test_terminal_state_has_double_border(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model')
        nodes = {n['id']: n for n in graph['nodes']}

        self.assertEqual(nodes['cancelled']['peripheries'], '2')
        self.assertEqual(nodes['open']['peripheries'], '1')

    def test_shared_sources_meet_in_a_junction(self):
        self.doc['transitions'] += [
            transition('remove', ['open', 'full'], 'new'),
            transition('succeed', ['open', 'full'], 'succeeded', automatic=True),
        ]
        graph = docs_graphs.lifecycle_graph(self.doc, 'model')

        junctions = [n for n in graph['nodes'] if n['id'].startswith('j')]
        self.assertEqual(len(junctions), 1)
        feeders = [e for e in graph['edges'] if e['target'] == junctions[0]['id']]
        self.assertEqual(sorted(e['source'] for e in feeders), ['full', 'open'])
        self.assertEqual(
            sorted(e['target'] for e in graph['edges'] if e['source'] == junctions[0]['id']),
            ['new', 'succeeded']
        )

    def test_whole_phase_is_one_edge(self):
        doc = {
            'states': [state(s) for s in [
                'draft', 'needs_work', 'submitted', 'open', 'succeeded', 'cancelled', 'rejected'
            ]],
            'transitions': [
                transition('approve', ['draft', 'needs_work', 'submitted'], 'open'),
                transition('succeed', ['open'], 'succeeded', automatic=True),
                transition('restore', ['cancelled', 'rejected'], 'draft'),
            ],
        }
        graph = docs_graphs.lifecycle_graph(doc, 'model')

        approve = edges_named(graph, 'approve')
        self.assertEqual(len(approve), 1)
        self.assertEqual(approve[0]['ltail'], 'cluster_setup')
        self.assertEqual([c['id'] for c in graph['clusters']], ['setup', 'stopped'])
        self.assertEqual(graph['ranks'], [('max', ['cancelled', 'rejected'])])

    def test_small_machines_have_no_phases(self):
        graph = docs_graphs.lifecycle_graph(self.doc, 'model')

        self.assertEqual(graph['clusters'], [])

    def test_variants(self):
        variants = docs_graphs.lifecycle_variants(self.doc, 'model')

        self.assertEqual(sorted(variants), ['a0g0', 'a0g1', 'a1g0', 'a1g1'])
        self.assertNotIn('Lock', variants['a0g0'])
        self.assertIn('Lock', variants['a1g0'])


class EffectsGraphTestCase(SimpleTestCase):
    def effect(self, kind, label, conditions=''):
        return {'graph': {'kind': kind, 'label': label, 'conditions': conditions}}

    def test_effects_are_grouped_by_kind(self):
        cancel = transition('cancel', ['open'], 'cancelled')
        cancel['effects'] = [
            self.effect('related', 'participants → cancel', 'there are participants'),
            self.effect('notification', 'ActivityCancelledNotification'),
            self.effect('notification', 'ActivityCancelledNotification'),
            {'graph': None},
        ]
        cancel['incoming'] = [{'label': 'Slot: cancel', 'url': '#slot-trans-cancel', 'conditions': ''}]
        graph = docs_graphs.effects_graph(cancel, 'model')

        self.assertEqual(
            [(c['id'], len(c['nodes'])) for c in graph['clusters']],
            [('incoming', 1), ('related', 1), ('notification', 1)]
        )
        related = next(e for e in graph['edges'] if e['target'] == 'related0')
        self.assertEqual(related['label'], 'if there are participants')

    def test_no_effects(self):
        self.assertIsNone(docs_graphs.effects_graph(transition('cancel', ['open'], 'cancelled'), 'model'))


class CascadeGraphTestCase(SimpleTestCase):
    def entry(self, model, name, *targets, relation='related'):
        return {
            'model': model, 'name': name, 'url': '#' + name, 'notifications': 0,
            'related': [{'relation': relation, 'conditions': '', 'targets': list(targets)}] if targets else [],
        }

    def test_cycle_is_drawn_once(self):
        index = {
            ('a', 'cancel'): self.entry('A', 'cancel', ('b', 'cancel')),
            ('b', 'cancel'): self.entry('B', 'cancel', ('a', 'cancel')),
        }
        graph = docs_graphs.cascade_graph(index, ('a', 'cancel'))

        self.assertEqual(sum(len(c['nodes']) for c in graph['clusters']), 2)
        self.assertEqual(len(graph['edges']), 2)

    def test_depth_limit(self):
        index = {
            ('m{}'.format(i), 't'): self.entry('M{}'.format(i), 't', ('m{}'.format(i + 1), 't'))
            for i in range(6)
        }
        index[('m6', 't')] = self.entry('M6', 't')
        graph = docs_graphs.cascade_graph(index, ('m0', 't'), depth=2)

        self.assertEqual(len(graph['clusters']), 3)
        self.assertEqual(graph['truncated'], 1)

    def test_no_related_effects(self):
        index = {('a', 't'): self.entry('A', 't')}

        self.assertIsNone(docs_graphs.cascade_graph(index, ('a', 't')))


class ToDotTestCase(SimpleTestCase):
    def setUp(self):
        self.graph = {
            'attrs': {'rankdir': 'LR'},
            'nodes': [{'id': 'a', 'label': 'Say "hi"', 'url': '#a'}],
            'edges': [{'source': 'a', 'target': 'b', 'label': 'back\\slash'}],
            'clusters': [{'id': 'c', 'label': 'Cluster', 'fillcolor': 'white', 'nodes': [{'id': 'b', 'label': 'B'}]}],
        }

    def test_quoting(self):
        dot = docs_graphs.to_dot(self.graph)

        self.assertIn('"a" [label="Say \\"hi\\"", URL="#a"', dot)
        self.assertIn('label="back\\\\slash"', dot)
        self.assertIn('subgraph "cluster_c"', dot)

    def test_dot_parses(self):
        if not shutil.which('dot'):
            self.skipTest('graphviz is not installed')
        result = subprocess.run(['dot', '-Tsvg'], input=docs_graphs.to_dot(self.graph).encode(), capture_output=True)

        self.assertEqual(result.returncode, 0, result.stderr)


class GraphIndexTestCase(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        models = get_fsm_models_for_apps(['time_based', 'deeds'])
        cls.docs = {model.__name__: document_fsm_enriched(model) for model in models}
        cls.index = build_graph_index([
            (model, cls.docs[model.__name__]) for model in models
        ])

    def related(self, key, relation):
        return next(r for r in self.index[key]['related'] if r['relation'] == relation)

    def test_related_property_resolves_to_family_member(self):
        related = self.related(('dateactivity', 'cancel'), 'accepted_participants')

        self.assertEqual(related['targets'], [('dateparticipant', 'cancel')])

    def test_polymorphic_relation_resolves_to_concrete_activity(self):
        related = [
            r for entry_key, entry in self.index.items() if entry_key[0] == 'dateparticipant'
            for r in entry['related'] if r['relation'] == 'activity'
        ]

        self.assertTrue(related)
        for r in related:
            self.assertEqual({target[0] for target in r['targets']}, {'dateactivity'})

    def test_incoming_from_other_models(self):
        cancel = next(t for t in self.docs['DateParticipant']['transitions'] if t['id'] == 'cancel')

        self.assertIn('#dateactivity-trans-cancel', [i.get('url') for i in cancel['incoming']])

    def test_effect_on_missing_relation_is_left_out(self):
        effects = [
            effect for t in self.docs['Deed']['transitions'] for effect in t['effects']
            if getattr(effect['effect_cls'], 'relation', None) == 'slots'
        ]

        self.assertTrue(effects)
        self.assertTrue(all(effect['graph'] is None for effect in effects))


class GenerateFsmDocsTestCase(BluebottleTestCase):
    def test_generates_graphs_for_every_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'fsm.html')
            call_command('generate_fsm_docs', '--app', 'time_based', '--output', path, stdout=open(os.devnull, 'w'))
            with open(path) as f:
                html = f.read()

        for model in get_fsm_models_for_apps(['time_based']):
            self.assertIn('id="{}-lifecycle-dots"'.format(model._meta.model_name), html)
        self.assertIn('id="family-date-activities-map"', html)
        self.assertIn('id="dateactivity-trans-cancel-cascade"', html)
        self.assertIn('viz-global.js', html)
