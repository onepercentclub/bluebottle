from graphviz import Digraph

from bluebottle.fsm.triggers import TransitionTrigger
from bluebottle.fsm.utils import clean, setup_instance
from bluebottle.time_based.models import Team

instance = setup_instance(Team)

machine = instance.states
states = []
transitions = []

for state in list(machine.states.values()):
    states.append(state.name.capitalize())


for transition in machine.transitions.values():
    sources = transition.sources
    if not isinstance(sources, (list, tuple)):
        sources = (sources,)

    for source in sources:
        triggers = [
            trigger for trigger in instance.triggers.triggers
            if isinstance(trigger, TransitionTrigger) and trigger.transition == transition
        ]
        effects = sum([trigger.effects for trigger in triggers], [])
        transitions.append((
            source.name.capitalize(),
            transition.target.name.capitalize(),
            transition.name,
            [clean(effect(instance).to_html()) for effect in effects]
        ))

# Create the FSM graph
fsm = Digraph("FSM", filename="fsm_with_multi_effects", format="png")
fsm.attr(rankdir='LR', size='12,8', dpi='600')  # Higher resolution and larger canvas

# Add states (nodes)
for state in states:
    fsm.node(state, shape='ellipse', style='filled', color='lightblue')

# Add transitions as separate nodes
for source, target, trigger, effects in transitions:
    # Create a unique name for the transition node
    transition_node = f"transition_{source}_{target}"
    fsm.node(
        transition_node,
        label=f"{trigger}",
        shape='diamond',
        style='filled',
        color='lightyellow'
    )

    # Connect states to transition nodes
    fsm.edge(source, transition_node, style='solid')
    fsm.edge(transition_node, target, style='solid')

    # If there are effects, add each effect as a separate node
    if effects:
        for idx, effect in enumerate(effects):
            effect_node = f"effect_{source}_{target}_{idx}"
            fsm.node(effect_node, label=effect, shape='note', style='filled', color='lightgreen')
            fsm.edge(transition_node, effect_node, style='dashed', color='gray')

# Render and save the FSM diagram
fsm.render(view=True)
