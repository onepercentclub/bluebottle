#!/usr/bin/env python3
"""
Universal FSM Documentation Generator
Generates HTML documentation for all Finite State Machine models in the Bluebottle codebase.
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bluebottle.settings.local')

try:
    django.setup()
except Exception as e:
    print(f"Warning: Django setup failed: {e}")
    print("Continuing anyway...")

from collections import defaultdict
import inspect


def get_all_state_machines():
    """
    Discover all registered state machines in the codebase.
    Returns a dict mapping model names to their state machine classes.
    """
    from bluebottle.fsm.state import _registry
    
    state_machines = {}
    for model, machine in _registry.items():
        model_name = model.__name__
        state_machines[model_name] = {
            'model': model,
            'machine': machine,
            'module': model.__module__,
        }
    
    return state_machines


def get_all_triggers():
    """
    Discover all registered triggers in the codebase.
    Returns a dict mapping model names to their trigger classes.
    """
    from bluebottle.fsm.triggers import _triggers
    
    triggers_map = {}
    for model, trigger_class in _triggers.items():
        model_name = model.__name__
        triggers_map[model_name] = {
            'model': model,
            'triggers': trigger_class,
            'module': model.__module__,
        }
    
    return triggers_map


def get_state_info(state):
    """Extract information from a State object."""
    return {
        'name': str(state.name),
        'value': state.value,
        'description': str(state.description) if state.description else '',
    }


def get_condition_description(condition):
    """Extract description from a condition function."""
    if condition is None:
        return None
    
    if hasattr(condition, '__doc__') and condition.__doc__:
        # Get first line of docstring
        doc = condition.__doc__.strip().split('\n')[0]
        return f"{condition.__name__} - {doc}"
    
    return condition.__name__


def get_permission_description(permission):
    """Extract description from a permission function."""
    if permission is None:
        return None
    
    if hasattr(permission, '__doc__') and permission.__doc__:
        # Get first line of docstring
        doc = permission.__doc__.strip().split('\n')[0]
        return f"{permission.__name__} - {doc}"
    
    return permission.__name__


def get_transition_info(transition, machine_instance):
    """Extract information from a Transition object."""
    info = {
        'name': transition.name,
        'description': str(transition.description) if transition.description else '',
        'automatic': transition.automatic,
        'sources': [],
        'target': None,
        'conditions': [],
        'permission': None,
    }
    
    # Get source states
    if hasattr(transition, 'source'):
        if hasattr(transition.source, '__iter__'):
            for source in transition.source:
                if hasattr(source, 'name'):
                    info['sources'].append(get_state_info(source))
        elif hasattr(transition.source, 'name'):
            info['sources'].append(get_state_info(transition.source))
    
    # Get target state
    if hasattr(transition, 'target') and hasattr(transition.target, 'name'):
        info['target'] = get_state_info(transition.target)
    
    # Get conditions
    if hasattr(transition, 'conditions'):
        for condition in transition.conditions:
            desc = get_condition_description(condition)
            if desc:
                info['conditions'].append(desc)
    
    # Get permission
    if hasattr(transition, 'permission') and transition.permission:
        info['permission'] = get_permission_description(transition.permission)
    
    return info


def get_message_info(message_class):
    """Extract information from a message class."""
    info = {
        'name': message_class.__name__,
        'subject': None,
        'recipients': 'Unknown',
    }
    
    try:
        # Try to get subject
        if hasattr(message_class, 'subject'):
            info['subject'] = str(message_class.subject)
        
        # Try to get recipient info from get_recipients method
        if hasattr(message_class, 'get_recipients'):
            source = inspect.getsource(message_class.get_recipients)
            # Simple heuristic to extract recipient info
            if 'owner' in source.lower():
                info['recipients'] = 'Activity owner'
            elif 'user' in source.lower() and 'participant' in source.lower():
                info['recipients'] = 'Participant user'
            elif 'participant' in source.lower():
                info['recipients'] = 'Participants'
            elif 'reviewer' in source.lower() or 'staff' in source.lower():
                info['recipients'] = 'Reviewer/Staff'
    except:
        pass
    
    return info


def get_effect_info(effect):
    """Extract information from an effect."""
    effect_type = type(effect).__name__
    
    info = {
        'type': effect_type,
        'description': '',
        'conditions': [],
    }
    
    # Handle different effect types
    if effect_type == 'TransitionEffect':
        if hasattr(effect, 'transition'):
            info['description'] = f"Trigger {effect.transition.name} transition"
        if hasattr(effect, 'conditions'):
            for condition in effect.conditions:
                desc = get_condition_description(condition)
                if desc:
                    info['conditions'].append(desc)
    
    elif effect_type == 'RelatedTransitionEffect':
        relation = getattr(effect, 'relation', 'related')
        transition_name = getattr(effect, 'transition', {}).get('name', 'unknown')
        info['description'] = f"Trigger {transition_name} on {relation}"
        if hasattr(effect, 'conditions'):
            for condition in effect.conditions:
                desc = get_condition_description(condition)
                if desc:
                    info['conditions'].append(desc)
    
    elif effect_type == 'NotificationEffect':
        if hasattr(effect, 'message_class'):
            message_info = get_message_info(effect.message_class)
            info['message'] = message_info
            if hasattr(effect, 'conditions'):
                for condition in effect.conditions:
                    desc = get_condition_description(condition)
                    if desc:
                        info['conditions'].append(desc)
    
    else:
        # Generic effect
        info['description'] = effect_type
    
    return info


def get_trigger_info(trigger_class):
    """Extract all triggers for a model."""
    triggers_list = []
    
    if not hasattr(trigger_class, 'triggers'):
        return triggers_list
    
    for trigger in trigger_class.triggers:
        trigger_type = type(trigger).__name__
        
        trigger_info = {
            'type': trigger_type,
            'field': None,
            'transition': None,
            'effects': [],
        }
        
        if trigger_type == 'ModelChangedTrigger':
            trigger_info['field'] = getattr(trigger, 'field', 'unknown')
        elif trigger_type == 'TransitionTrigger':
            if hasattr(trigger, 'transition'):
                trigger_info['transition'] = trigger.transition.name
        elif trigger_type == 'ModelDeletedTrigger':
            trigger_info['type'] = 'ModelDeletedTrigger'
        
        # Get effects
        if hasattr(trigger, 'effects'):
            for effect in trigger.effects:
                effect_info = get_effect_info(effect)
                trigger_info['effects'].append(effect_info)
        
        triggers_list.append(trigger_info)
    
    return triggers_list


def generate_state_color(state_value):
    """Generate a color for a state based on its value."""
    color_map = {
        'draft': '#28a745',
        'submitted': '#6c757d',
        'needs_work': '#ffc107',
        'open': '#17a2b8',
        'succeeded': '#28a745',
        'failed': '#dc3545',
        'cancelled': '#6c757d',
        'rejected': '#dc3545',
        'expired': '#6c757d',
        'full': '#fd7e14',
        'partially_funded': '#ffc107',
        'refunded': '#6c757d',
        'accepted': '#17a2b8',
        'withdrawn': '#6c757d',
        'removed': '#dc3545',
        'new': '#17a2b8',
        'pending': '#ffc107',
        'scheduled': '#17a2b8',
        'finished': '#28a745',
        'running': '#17a2b8',
        'verified': '#28a745',
        'unverified': '#ffc107',
        'incomplete': '#ffc107',
        'planned': '#17a2b8',
    }
    return color_map.get(state_value, '#007bff')


def generate_html_for_model(model_name, machine_info, triggers_info, output_dir):
    """Generate HTML documentation for a single model."""
    machine_class = machine_info['machine']
    
    # Get all states
    states = []
    for attr_name in dir(machine_class):
        attr = getattr(machine_class, attr_name)
        if hasattr(attr, '__class__') and attr.__class__.__name__ == 'State':
            state_info = get_state_info(attr)
            states.append({
                'attr_name': attr_name,
                **state_info
            })
    
    # Get all transitions
    transitions = []
    for attr_name in dir(machine_class):
        attr = getattr(machine_class, attr_name)
        if hasattr(attr, '__class__') and attr.__class__.__name__ == 'Transition':
            # Create a dummy instance to access transition details
            try:
                machine_instance = machine_class()
                transition_info = get_transition_info(attr, machine_instance)
                transitions.append({
                    'attr_name': attr_name,
                    **transition_info
                })
            except:
                pass
    
    # Get triggers
    triggers = []
    if triggers_info:
        triggers = get_trigger_info(triggers_info['triggers'])
    
    # Generate individual state pages
    for state in states:
        generate_state_page(model_name, state, states, transitions, triggers, output_dir)
    
    return states, transitions


def generate_state_page(model_name, state, all_states, all_transitions, all_triggers, output_dir):
    """Generate an individual page for a state."""
    state_value = state['value']
    state_name = state['name']
    state_description = state['description']
    
    # Find outgoing transitions
    outgoing_transitions = []
    for trans in all_transitions:
        for source in trans['sources']:
            if source['value'] == state_value:
                outgoing_transitions.append(trans)
                break
    
    # Find incoming transitions
    incoming_transitions = []
    for trans in all_transitions:
        if trans['target'] and trans['target']['value'] == state_value:
            incoming_transitions.append(trans)
    
    # Find relevant triggers for this state
    relevant_triggers = []
    for trigger in all_triggers:
        if trigger['transition'] and trigger['transition'] in [t['name'] for t in outgoing_transitions + incoming_transitions]:
            relevant_triggers.append(trigger)
    
    # Generate HTML
    color = generate_state_color(state_value)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} - {state_name}</title>
    <link rel="stylesheet" href="../shared_styles.css">
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to All Models</a>
        
        <header class="state-header" style="border-left: 3px solid {color};">
            <h1>{state_name}</h1>
            <div class="model-name">{model_name}</div>
            <div class="state-value">{state_value}</div>
            <p class="state-description">{state_description}</p>
        </header>
"""
    
    # Outgoing transitions
    if outgoing_transitions:
        html += """
        <div class="section">
            <h2>📤 Outgoing Transitions</h2>
"""
        for trans in outgoing_transitions:
            trans_type = 'automatic' if trans['automatic'] else 'manual'
            html += f"""
            <div class="transition-card {trans_type}">
                <div class="transition-header">
                    <span class="transition-name">{trans['name']}</span>
                    <span class="transition-type">{'Automatic' if trans['automatic'] else 'Manual'}</span>
                </div>
"""
            if trans['target']:
                target_file = f"{model_name.lower()}_{trans['target']['value']}.html"
                html += f"""
                <div class="transition-to">
                    → <a href="{target_file}" class="state-link">{trans['target']['name']}</a>
                </div>
"""
            
            if trans['description']:
                html += f"""
                <div class="transition-description">{trans['description']}</div>
"""
            
            if trans['permission']:
                html += f"""
                <div class="details-section">
                    <h4>🔐 Permission Required</h4>
                    <ul>
                        <li><code>{trans['permission']}</code></li>
                    </ul>
                </div>
"""
            
            if trans['conditions']:
                html += """
                <div class="details-section">
                    <h4>✅ Conditions</h4>
                    <ul>
"""
                for condition in trans['conditions']:
                    html += f"                        <li><code>{condition}</code></li>\n"
                html += """                    </ul>
                </div>
"""
            
            # Find effects for this transition
            trans_effects = []
            for trigger in all_triggers:
                if trigger['transition'] == trans['name']:
                    trans_effects.extend(trigger['effects'])
            
            if trans_effects:
                html += """
                <div class="details-section">
                    <h4>⚡ Effects</h4>
                    <ul class="effects-list">
"""
                for effect in trans_effects:
                    html += f"""                        <li class="effect-item">
                            <div class="effect-type">{effect['type']}</div>
"""
                    if effect.get('message'):
                        msg = effect['message']
                        html += f"""                            <div class="notification-subject">Subject: {msg['subject']}</div>
                            <div class="notification-recipient">Recipient: {msg['recipients']}</div>
"""
                    elif effect['description']:
                        html += f"""                            <div>{effect['description']}</div>
"""
                    
                    if effect.get('conditions'):
                        html += f"""                            <div class="notification-condition">Condition: {', '.join(effect['conditions'])}</div>
"""
                    html += """                        </li>
"""
                html += """                    </ul>
                </div>
"""
            
            html += """            </div>
"""
        html += """        </div>
"""
    
    # Incoming transitions
    if incoming_transitions:
        html += """
        <div class="section">
            <h2>📥 Incoming Transitions</h2>
            <ul class="incoming-list">
"""
        for trans in incoming_transitions:
            source_states = ', '.join([s['name'] for s in trans['sources']])
            html += f"""                <li class="incoming-item">
                    <strong>{trans['name']}</strong> from {source_states}
                </li>
"""
        html += """            </ul>
        </div>
"""
    
    html += """    </div>
</body>
</html>"""
    
    # Write to file
    filename = f"{model_name.lower()}_{state_value}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(html)


def generate_index_page(all_models_info, output_dir):
    """Generate the main index page listing all models."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bluebottle FSM Documentation</title>
    <link rel="stylesheet" href="shared_styles.css">
</head>
<body>
    <div class="container">
        <header class="main-header">
            <h1>Bluebottle Finite State Machine Documentation</h1>
            <p>Interactive documentation for all FSM models in the Bluebottle platform</p>
        </header>
"""
    
    # Group models by category
    categories = {
        'Time-Based Activities': ['DateActivity', 'DeadlineActivity', 'ScheduleActivity', 'PeriodicActivity', 'RegisteredDateActivity'],
        'Time-Based Participants': ['DateParticipant', 'DeadlineParticipant', 'ScheduleParticipant', 'TeamScheduleParticipant', 'PeriodicParticipant', 'RegisteredDateParticipant'],
        'Funding': ['Funding', 'Donor', 'Payment', 'Payout', 'PlainPayoutAccount', 'MoneyContribution'],
        'Collect Activities': ['CollectActivity', 'CollectContributor', 'CollectContribution'],
        'Deeds': ['Deed', 'DeedParticipant'],
        'Other': [],
    }
    
    # Categorize models
    categorized = {cat: [] for cat in categories}
    uncategorized = []
    
    for model_name, info in all_models_info.items():
        found = False
        for cat, models in categories.items():
            if model_name in models:
                categorized[cat].append((model_name, info))
                found = True
                break
        if not found:
            uncategorized.append((model_name, info))
    
    # Add uncategorized to "Other"
    categorized['Other'] = uncategorized
    
    # Generate HTML for each category
    for category, models in categorized.items():
        if not models:
            continue
        
        html += f"""
        <div class="category-section">
            <h2>{category}</h2>
            <div class="model-grid">
"""
        
        for model_name, info in sorted(models, key=lambda x: x[0]):
            model_dir = model_name.lower()
            states = info['states']
            
            html += f"""
                <div class="model-card">
                    <h3>{model_name}</h3>
                    <div class="state-count">{len(states)} states</div>
                    <div class="state-list">
"""
            
            for state in states[:5]:  # Show first 5 states
                color = generate_state_color(state['value'])
                state_file = f"{model_dir}/{model_name.lower()}_{state['value']}.html"
                html += f"""                        <a href="{state_file}" class="state-badge" style="border-left-color: {color};">{state['name']}</a>
"""
            
            if len(states) > 5:
                html += f"""                        <span class="more-states">+{len(states) - 5} more</span>
"""
            
            html += """                    </div>
                </div>
"""
        
        html += """            </div>
        </div>
"""
    
    html += """    </div>
</body>
</html>"""
    
    # Write to file
    filepath = os.path.join(output_dir, 'index.html')
    with open(filepath, 'w') as f:
        f.write(html)


def generate_shared_css(output_dir):
    """Generate shared CSS file."""
    css = """/* Bluebottle FSM Documentation - Shared Styles */

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
    padding: 20px;
    line-height: 1.5;
    margin: 0;
}

.container {
    max-width: 1000px;
    margin: 0 auto;
}

.back-link {
    display: inline-block;
    color: #007bff;
    text-decoration: none;
    margin-bottom: 20px;
    font-size: 14px;
}

.back-link:hover {
    text-decoration: underline;
}

.main-header {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 30px;
    margin-bottom: 30px;
    text-align: center;
}

.main-header h1 {
    margin: 0 0 10px 0;
    color: #333;
    font-size: 28px;
}

.main-header p {
    margin: 0;
    color: #666;
    font-size: 16px;
}

.state-header {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 25px;
    margin-bottom: 20px;
}

.state-header h1 {
    margin: 0 0 5px 0;
    color: #333;
    font-size: 32px;
}

.model-name {
    display: inline-block;
    background: #e9ecef;
    padding: 4px 12px;
    border-radius: 3px;
    font-size: 13px;
    color: #666;
    margin-bottom: 10px;
}

.state-value {
    display: inline-block;
    background: #e9ecef;
    padding: 4px 12px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #495057;
    margin-bottom: 10px;
    margin-left: 10px;
}

.state-description {
    margin: 15px 0 0 0;
    color: #666;
    font-size: 15px;
}

.section {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 25px;
    margin-bottom: 20px;
}

.section h2 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 20px;
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 10px;
}

.transition-card {
    background: #fafafa;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 18px;
    margin-bottom: 15px;
    border-left: 3px solid #666;
}

.transition-card.manual {
    border-left-color: #007bff;
}

.transition-card.automatic {
    border-left-color: #28a745;
}

.transition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.transition-name {
    font-weight: 600;
    font-size: 16px;
    color: #333;
}

.transition-type {
    background: #e9ecef;
    padding: 3px 10px;
    border-radius: 3px;
    font-size: 12px;
    color: #666;
}

.transition-to {
    margin-bottom: 10px;
    font-size: 15px;
    color: #666;
}

.state-link {
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
}

.state-link:hover {
    text-decoration: underline;
}

.transition-description {
    color: #666;
    margin-bottom: 15px;
    font-size: 14px;
    font-style: italic;
}

.details-section {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #e9ecef;
}

.details-section h4 {
    margin: 0 0 10px 0;
    color: #666;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
}

.details-section ul {
    margin: 0;
    padding-left: 20px;
}

.details-section li {
    margin-bottom: 5px;
    font-size: 14px;
}

code {
    background: #f8f9fa;
    padding: 2px 6px;
    border-radius: 2px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #e83e8c;
}

.effects-list {
    list-style: none;
    padding: 0;
}

.effect-item {
    background: #f8f9fa;
    padding: 10px;
    border-radius: 3px;
    margin-bottom: 10px;
    font-size: 14px;
}

.effect-type {
    font-weight: 600;
    color: #007bff;
    margin-bottom: 5px;
}

.notification-subject {
    color: #333;
    margin-bottom: 3px;
}

.notification-recipient {
    color: #666;
    font-size: 13px;
    margin-bottom: 3px;
}

.notification-condition {
    color: #856404;
    font-size: 12px;
    font-style: italic;
    margin-top: 5px;
}

.incoming-list {
    list-style: none;
    padding: 0;
}

.incoming-item {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 3px;
    margin-bottom: 10px;
    border-left: 3px solid #17a2b8;
}

.category-section {
    margin-bottom: 40px;
}

.category-section h2 {
    color: #333;
    font-size: 24px;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #ddd;
}

.model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.model-card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 20px;
    transition: box-shadow 0.2s;
}

.model-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.model-card h3 {
    margin: 0 0 10px 0;
    color: #333;
    font-size: 18px;
}

.state-count {
    color: #666;
    font-size: 13px;
    margin-bottom: 15px;
}

.state-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.state-badge {
    display: inline-block;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-left: 3px solid;
    padding: 4px 10px;
    border-radius: 3px;
    text-decoration: none;
    color: #495057;
    font-size: 12px;
    transition: background-color 0.2s;
}

.state-badge:hover {
    background: #e9ecef;
}

.more-states {
    color: #666;
    font-size: 12px;
    padding: 4px 10px;
}
"""
    
    filepath = os.path.join(output_dir, 'shared_styles.css')
    with open(filepath, 'w') as f:
        f.write(css)


def main():
    """Main function to generate all documentation."""
    print("🚀 Universal FSM Documentation Generator")
    print("=" * 60)
    
    # Create output directory
    output_base = 'fsm_documentation'
    if not os.path.exists(output_base):
        os.makedirs(output_base)
    
    # Get all state machines and triggers
    print("\n📊 Discovering state machines...")
    state_machines = get_all_state_machines()
    print(f"   Found {len(state_machines)} state machine(s)")
    
    print("\n📊 Discovering triggers...")
    triggers_map = get_all_triggers()
    print(f"   Found {len(triggers_map)} trigger class(es)")
    
    # Generate documentation for each model
    print("\n📝 Generating documentation...")
    all_models_info = {}
    
    for model_name in sorted(state_machines.keys()):
        print(f"\n   Processing {model_name}...")
        
        machine_info = state_machines[model_name]
        triggers_info = triggers_map.get(model_name)
        
        # Create model directory
        model_dir = os.path.join(output_base, model_name.lower())
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        try:
            states, transitions = generate_html_for_model(
                model_name, 
                machine_info, 
                triggers_info, 
                model_dir
            )
            
            all_models_info[model_name] = {
                'states': states,
                'transitions': transitions,
                'machine': machine_info,
                'triggers': triggers_info,
            }
            
            print(f"      ✓ Generated {len(states)} state pages")
        except Exception as e:
            print(f"      ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate shared CSS
    print("\n🎨 Generating shared styles...")
    generate_shared_css(output_base)
    
    # Generate index page
    print("\n📄 Generating index page...")
    generate_index_page(all_models_info, output_base)
    
    print("\n" + "=" * 60)
    print(f"✅ Documentation generated successfully!")
    print(f"📁 Output directory: {output_base}/")
    print(f"🌐 Open {output_base}/index.html to view the documentation")
    print("=" * 60)


if __name__ == '__main__':
    main()

