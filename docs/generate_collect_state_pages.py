#!/usr/bin/env python3
"""
Generate HTML documentation for CollectActivity and CollectContributor state machines.
Based on the proven approach used for Deed documentation.
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

from bluebottle.collect.models import CollectActivity, CollectContributor
from bluebottle.collect.states import CollectActivityStateMachine, CollectContributorStateMachine
from bluebottle.activities.states import ActivityStateMachine, ContributorStateMachine


def get_state_color(state_value):
    """Get color for a state."""
    colors = {
        'draft': '#28a745',
        'submitted': '#6c757d',
        'needs_work': '#ffc107',
        'open': '#17a2b8',
        'succeeded': '#28a745',
        'failed': '#dc3545',
        'cancelled': '#6c757d',
        'rejected': '#dc3545',
        'expired': '#6c757d',
        'accepted': '#17a2b8',
        'withdrawn': '#6c757d',
        'new': '#17a2b8',
    }
    return colors.get(state_value, '#007bff')


def generate_activity_pages():
    """Generate pages for CollectActivity states."""
    print("\n📝 Generating CollectActivity state pages...")
    
    machine = CollectActivityStateMachine
    
    # Get all states
    states = [
        ('draft', machine.draft),
        ('submitted', machine.submitted),
        ('needs_work', machine.needs_work),
        ('open', machine.open),
        ('succeeded', machine.succeeded),
        ('cancelled', machine.cancelled),
        ('rejected', machine.rejected),
        ('expired', machine.expired),
    ]
    
    # Get all transitions
    transitions = {
        'initiate': machine.initiate,
        'submit': machine.submit,
        'approve': machine.approve,
        'auto_approve': machine.auto_approve,
        'publish': machine.publish,
        'auto_publish': machine.auto_publish,
        'succeed': machine.succeed,
        'succeed_manually': machine.succeed_manually,
        'expire': machine.expire,
        'cancel': machine.cancel,
        'reject': machine.reject,
        'restore': machine.restore,
        'reopen': machine.reopen,
        'reopen_manually': machine.reopen_manually,
        'request_changes': machine.request_changes,
        'delete': machine.delete,
    }
    
    output_dir = 'collect_states_visualization'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate individual state pages
    for state_value, state in states:
        generate_state_page(
            'CollectActivity',
            state_value,
            state,
            states,
            transitions,
            output_dir
        )
    
    print(f"   ✓ Generated {len(states)} CollectActivity state pages")


def generate_contributor_pages():
    """Generate pages for CollectContributor states."""
    print("\n📝 Generating CollectContributor state pages...")
    
    machine = CollectContributorStateMachine
    
    # Get all states
    states = [
        ('new', machine.new),
        ('accepted', machine.accepted),
        ('succeeded', machine.succeeded),
        ('failed', machine.failed),
        ('withdrawn', machine.withdrawn),
        ('rejected', machine.rejected),
    ]
    
    # Get all transitions
    transitions = {
        'initiate': machine.initiate,
        'succeed': machine.succeed,
        'fail': machine.fail,
        'reset': machine.reset,
        'accept': machine.accept,
        're_accept': machine.re_accept,
        'withdraw': machine.withdraw,
        'reapply': machine.reapply,
        'remove': machine.remove,
    }
    
    output_dir = 'collect_states_visualization'
    
    # Generate individual state pages
    for state_value, state in states:
        generate_state_page(
            'CollectContributor',
            state_value,
            state,
            states,
            transitions,
            output_dir
        )
    
    print(f"   ✓ Generated {len(states)} CollectContributor state pages")


def generate_state_page(model_name, state_value, state, all_states, transitions, output_dir):
    """Generate an individual state page."""
    state_name = str(state.name)
    state_description = str(state.description) if state.description else ''
    
    # Find outgoing transitions
    outgoing = []
    for trans_name, trans in transitions.items():
        if hasattr(trans, 'source'):
            sources = trans.source if isinstance(trans.source, list) else [trans.source]
            for source in sources:
                if hasattr(source, 'value') and source.value == state_value:
                    target = trans.target if hasattr(trans, 'target') else None
                    outgoing.append({
                        'name': trans_name,
                        'display_name': str(trans.name) if hasattr(trans, 'name') else trans_name,
                        'target': target,
                        'description': str(trans.description) if hasattr(trans, 'description') else '',
                        'automatic': getattr(trans, 'automatic', True),
                        'conditions': [],
                        'permission': None,
                    })
                    break
    
    # Find incoming transitions
    incoming = []
    for trans_name, trans in transitions.items():
        target = trans.target if hasattr(trans, 'target') else None
        if target and hasattr(target, 'value') and target.value == state_value:
            sources = trans.source if isinstance(trans.source, list) else [trans.source]
            source_names = [str(s.name) if hasattr(s, 'name') else 'Unknown' for s in sources if hasattr(s, 'name')]
            incoming.append({
                'name': trans_name,
                'display_name': str(trans.name) if hasattr(trans, 'name') else trans_name,
                'sources': source_names,
            })
    
    # Generate HTML
    color = get_state_color(state_value)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} - {state_name}</title>
    <link rel="stylesheet" href="../deed_states_visualization/state_styles.css">
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Collect States</a>
        
        <header class="state-header" style="border-left: 3px solid {color};">
            <h1>{state_name}</h1>
            <div class="model-name">{model_name}</div>
            <div class="state-value">{state_value}</div>
            <p class="state-description">{state_description}</p>
        </header>
"""
    
    # Outgoing transitions
    if outgoing:
        html += """
        <div class="section">
            <h2>📤 Outgoing Transitions</h2>
"""
        for trans in outgoing:
            trans_type = 'automatic' if trans['automatic'] else 'manual'
            html += f"""
            <div class="transition-card {trans_type}">
                <div class="transition-header">
                    <span class="transition-name">{trans['display_name']}</span>
                    <span class="transition-type">{'Automatic' if trans['automatic'] else 'Manual'}</span>
                </div>
"""
            if trans['target'] and hasattr(trans['target'], 'value'):
                target_file = f"{model_name.lower()}_{trans['target'].value}.html"
                target_name = str(trans['target'].name) if hasattr(trans['target'], 'name') else trans['target'].value
                html += f"""
                <div class="transition-to">
                    → <a href="{target_file}" class="state-link">{target_name}</a>
                </div>
"""
            
            if trans['description']:
                html += f"""
                <div class="transition-description">{trans['description']}</div>
"""
            
            html += """            </div>
"""
        html += """        </div>
"""
    
    # Incoming transitions
    if incoming:
        html += """
        <div class="section">
            <h2>📥 Incoming Transitions</h2>
            <ul class="incoming-list">
"""
        for trans in incoming:
            sources = ', '.join(trans['sources']) if trans['sources'] else 'Unknown'
            html += f"""                <li class="incoming-item">
                    <strong>{trans['display_name']}</strong> from {sources}
                </li>
"""
        html += """            </ul>
        </div>
"""
    
    html += """    </div>
</body>
</html>"""
    
    # Write file
    filename = f"{model_name.lower()}_{state_value}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_index_page():
    """Generate index page for Collect documentation."""
    print("\n📄 Generating index page...")
    
    output_dir = 'collect_states_visualization'
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Collect States Documentation</title>
    <link rel="stylesheet" href="../deed_states_visualization/state_styles.css">
</head>
<body>
    <div class="container">
        <header class="main-header">
            <h1>Collect States Documentation</h1>
            <p>Interactive documentation for CollectActivity and CollectContributor state machines</p>
        </header>
        
        <div class="category-section">
            <h2>CollectActivity States</h2>
            <div class="model-grid">
"""
    
    activity_states = [
        ('draft', 'Draft', 'Activity created, not yet completed'),
        ('submitted', 'Submitted', 'Activity submitted for review'),
        ('needs_work', 'Needs Work', 'Activity needs modifications'),
        ('open', 'Open', 'Activity published and accepting contributors'),
        ('succeeded', 'Succeeded', 'Activity completed successfully'),
        ('cancelled', 'Cancelled', 'Activity cancelled'),
        ('rejected', 'Rejected', 'Activity rejected by reviewers'),
        ('expired', 'Expired', 'Activity expired without contributors'),
    ]
    
    for state_value, state_name, description in activity_states:
        color = get_state_color(state_value)
        html += f"""
                <a href="collectactivity_{state_value}.html" class="state-card" style="border-left-color: {color};">
                    <div class="state-name">{state_name}</div>
                    <div class="state-value">{state_value}</div>
                    <div class="state-description">{description}</div>
                </a>
"""
    
    html += """
            </div>
        </div>
        
        <div class="category-section">
            <h2>CollectContributor States</h2>
            <div class="model-grid">
"""
    
    contributor_states = [
        ('new', 'New', 'New contribution'),
        ('accepted', 'Participating', 'Person signed up for activity'),
        ('succeeded', 'Succeeded', 'Successful contribution'),
        ('failed', 'Failed', 'Failed contribution'),
        ('withdrawn', 'Withdrawn', 'Person has cancelled'),
        ('rejected', 'Removed', 'Person removed from activity'),
    ]
    
    for state_value, state_name, description in contributor_states:
        color = get_state_color(state_value)
        html += f"""
                <a href="collectcontributor_{state_value}.html" class="state-card" style="border-left-color: {color};">
                    <div class="state-name">{state_name}</div>
                    <div class="state-value">{state_value}</div>
                    <div class="state-description">{description}</div>
                </a>
"""
    
    html += """
            </div>
        </div>
    </div>
</body>
</html>"""
    
    filepath = os.path.join(output_dir, 'index.html')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"   ✓ Generated index.html")


def main():
    """Main function."""
    print("=" * 70)
    print("🚀 Collect States Documentation Generator")
    print("=" * 70)
    
    generate_activity_pages()
    generate_contributor_pages()
    generate_index_page()
    
    print("\n" + "=" * 70)
    print("✅ Documentation generated successfully!")
    print("\n📁 Output directory: collect_states_visualization/")
    print("🌐 Open collect_states_visualization/index.html to view")
    print("=" * 70)


if __name__ == '__main__':
    main()

