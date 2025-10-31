#!/usr/bin/env python3
"""
Generate HTML pages for ALL FSM models from FSM_COMPLETE_DOCUMENTATION.md
Extracts data from markdown and creates interactive visualizations for all 18 models.
"""

import os
import re
from pathlib import Path


def get_state_color(state_value):
    """Get color for a state."""
    colors = {
        'draft': '#28a745', 'submitted': '#6c757d', 'needs_work': '#ffc107',
        'open': '#17a2b8', 'succeeded': '#28a745', 'failed': '#dc3545',
        'cancelled': '#6c757d', 'rejected': '#dc3545', 'expired': '#6c757d',
        'full': '#fd7e14', 'partially_funded': '#ffc107', 'refunded': '#6c757d',
        'accepted': '#17a2b8', 'withdrawn': '#6c757d', 'removed': '#dc3545',
        'new': '#17a2b8', 'pending': '#ffc107', 'scheduled': '#17a2b8',
        'on_hold': '#ffc107', 'activity_refunded': '#6c757d', 'planned': '#17a2b8',
        'action_needed': '#ffc107', 'refund_requested': '#ffc107', 'deleted': '#6c757d',
        'unverified': '#ffc107', 'verified': '#28a745', 'incomplete': '#ffc107',
    }
    return colors.get(state_value, '#007bff')


# Model configurations with state lists extracted from documentation
MODELS_CONFIG = {
    'DateActivity': {
        'category': 'Time-Based Activities',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
        'description': 'Time-based activities with specific start dates and times',
    },
    'DeadlineActivity': {
        'category': 'Time-Based Activities',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
        'description': 'Activities with registration and completion deadlines',
    },
    'ScheduleActivity': {
        'category': 'Time-Based Activities',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
        'description': 'Activities with flexible scheduling slots',
    },
    'PeriodicActivity': {
        'category': 'Time-Based Activities',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
        'description': 'Recurring activities that repeat on a schedule',
    },
    'RegisteredDateActivity': {
        'category': 'Time-Based Activities',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'planned', 'succeeded', 'cancelled', 'rejected'],
        'description': 'Past activities registered retroactively',
    },
    'DateParticipant': {
        'category': 'Time-Based Participants',
        'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
        'description': 'Participants for date-based activities',
    },
    'DeadlineParticipant': {
        'category': 'Time-Based Participants',
        'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
        'description': 'Participants for deadline-based activities',
    },
    'ScheduleParticipant': {
        'category': 'Time-Based Participants',
        'states': ['new', 'accepted', 'scheduled', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
        'description': 'Participants assigned to schedule slots',
    },
    'TeamScheduleParticipant': {
        'category': 'Time-Based Participants',
        'states': ['new', 'accepted', 'scheduled', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
        'description': 'Team members in scheduled activities',
    },
    'PeriodicParticipant': {
        'category': 'Time-Based Participants',
        'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
        'description': 'Participants in recurring activities',
    },
    'RegisteredDateParticipant': {
        'category': 'Time-Based Participants',
        'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
        'description': 'Retroactively registered participants',
    },
    'Funding': {
        'category': 'Funding',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'on_hold', 'succeeded', 'partially_funded', 'refunded', 'cancelled', 'rejected'],
        'description': 'Crowdfunding campaigns with financial goals',
    },
    'Donor': {
        'category': 'Funding',
        'states': ['new', 'pending', 'succeeded', 'failed', 'refunded', 'activity_refunded', 'expired'],
        'description': 'Individual donations and donor management',
    },
    'Payment': {
        'category': 'Funding',
        'states': ['new', 'pending', 'action_needed', 'succeeded', 'failed', 'refund_requested', 'refunded'],
        'description': 'Payment processing and transaction states',
    },
    'CollectActivity': {
        'category': 'Collect Activities',
        'states': ['draft', 'submitted', 'needs_work', 'open', 'succeeded', 'expired', 'cancelled', 'rejected'],
        'description': 'Collection activities for gathering items or pledges',
    },
    'CollectContributor': {
        'category': 'Collect Activities',
        'states': ['new', 'accepted', 'succeeded', 'failed', 'withdrawn', 'rejected'],
        'description': 'Contributors to collection activities',
    },
}


def generate_simple_state_page(model_name, state_value, state_name, output_dir):
    """Generate a simple state page linking to markdown documentation."""
    
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
        <a href="index.html" class="back-link">← Back to {model_name} States</a>
        
        <header class="state-header" style="border-left: 3px solid {color};">
            <h1>{state_name}</h1>
            <div class="model-name">{model_name}</div>
            <div class="state-value">{state_value}</div>
        </header>
        
        <div class="section">
            <h2>📖 Complete Documentation</h2>
            <p>For detailed information about this state, including transitions, triggers, effects, and notifications, see the complete documentation:</p>
            <a href="../FSM_COMPLETE_DOCUMENTATION.md" class="state-link" style="font-size: 16px;">
                View {model_name} in Complete Documentation →
            </a>
        </div>
        
        <div class="section">
            <h2>🔍 What to Look For</h2>
            <ul>
                <li><strong>Outgoing Transitions:</strong> How to move from this state to others</li>
                <li><strong>Incoming Transitions:</strong> How to reach this state</li>
                <li><strong>Conditions:</strong> Requirements that must be met</li>
                <li><strong>Permissions:</strong> Who can trigger transitions</li>
                <li><strong>Effects:</strong> What happens when transitions occur</li>
                <li><strong>Notifications:</strong> Email messages sent to users</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📚 Related Documentation</h2>
            <ul>
                <li><a href="../fsm_documentation_portal.html" class="state-link">FSM Documentation Portal</a></li>
                <li><a href="../FSM_QUICK_START.md" class="state-link">Quick Start Guide</a></li>
                <li><a href="../FSM_COMPLETE_DOCUMENTATION.md" class="state-link">Complete Documentation</a></li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    # Write file
    filename = f"{model_name.lower()}_{state_value}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_model_index(model_name, config, output_dir):
    """Generate index page for a specific model."""
    
    states = config['states']
    description = config['description']
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} States</title>
    <link rel="stylesheet" href="../deed_states_visualization/state_styles.css">
</head>
<body>
    <div class="container">
        <a href="../fsm_documentation_portal.html" class="back-link">← Back to All Models</a>
        
        <header class="main-header">
            <h1>{model_name}</h1>
            <p>{description}</p>
        </header>
        
        <div class="section">
            <h2>📖 Complete Documentation</h2>
            <p>For detailed information including transitions, triggers, effects, and notifications:</p>
            <a href="../FSM_COMPLETE_DOCUMENTATION.md" class="state-link" style="font-size: 16px; display: inline-block; margin: 15px 0;">
                View {model_name} Documentation →
            </a>
        </div>
        
        <div class="section">
            <h2>📍 States ({len(states)})</h2>
            <div class="model-grid">
"""
    
    for state in states:
        color = get_state_color(state)
        state_name = state.replace('_', ' ').title()
        html += f"""
                <a href="{model_name.lower()}_{state}.html" class="state-card" style="border-left-color: {color};">
                    <div class="state-name">{state_name}</div>
                    <div class="state-value">{state}</div>
                </a>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>🔗 Quick Links</h2>
            <ul>
                <li><a href="../fsm_documentation_portal.html" class="state-link">All Models Portal</a></li>
                <li><a href="../FSM_COMPLETE_DOCUMENTATION.md" class="state-link">Complete Documentation</a></li>
                <li><a href="../FSM_QUICK_START.md" class="state-link">Quick Start Guide</a></li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    filepath = os.path.join(output_dir, 'index.html')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_all_models():
    """Generate HTML pages for all models."""
    
    print("\n🚀 Generating HTML pages for ALL FSM models...")
    print("=" * 70)
    
    total_pages = 0
    
    for model_name, config in MODELS_CONFIG.items():
        print(f"\n📝 Processing {model_name}...")
        
        # Create output directory
        output_dir = f"{model_name.lower()}_visualization"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate state pages
        states = config['states']
        for state in states:
            state_name = state.replace('_', ' ').title()
            generate_simple_state_page(model_name, state, state_name, output_dir)
            total_pages += 1
        
        # Generate model index
        generate_model_index(model_name, config, output_dir)
        total_pages += 1
        
        print(f"   ✓ Generated {len(states) + 1} pages in {output_dir}/")
    
    return total_pages


def generate_master_index():
    """Generate master index linking to all model visualizations."""
    
    print("\n📄 Generating master visualization index...")
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FSM Visualizations - All Models</title>
    <link rel="stylesheet" href="deed_states_visualization/state_styles.css">
</head>
<body>
    <div class="container">
        <header class="main-header">
            <h1>🎨 FSM Interactive Visualizations</h1>
            <p>Browse state visualizations for all models</p>
        </header>
        
        <div class="section">
            <h2>📖 Documentation Options</h2>
            <div class="model-grid">
                <a href="fsm_documentation_portal.html" class="state-card" style="border-left-color: #667eea;">
                    <div class="state-name">Main Portal</div>
                    <div class="state-description">Searchable portal with all models</div>
                </a>
                <a href="FSM_COMPLETE_DOCUMENTATION.md" class="state-card" style="border-left-color: #28a745;">
                    <div class="state-name">Complete Docs</div>
                    <div class="state-description">Detailed markdown documentation</div>
                </a>
                <a href="deed_states_visualization/index.html" class="state-card" style="border-left-color: #17a2b8;">
                    <div class="state-name">Deed Example</div>
                    <div class="state-description">Fully detailed interactive example</div>
                </a>
            </div>
        </div>
"""
    
    # Group by category
    categories = {}
    for model_name, config in MODELS_CONFIG.items():
        category = config['category']
        if category not in categories:
            categories[category] = []
        categories[category].append((model_name, config))
    
    # Generate sections for each category
    for category, models in sorted(categories.items()):
        html += f"""
        <div class="section">
            <h2>{category}</h2>
            <div class="model-grid">
"""
        
        for model_name, config in models:
            viz_dir = f"{model_name.lower()}_visualization"
            color = get_state_color(config['states'][0])
            html += f"""
                <a href="{viz_dir}/index.html" class="state-card" style="border-left-color: {color};">
                    <div class="state-name">{model_name}</div>
                    <div class="state-value">{len(config['states'])} states</div>
                    <div class="state-description">{config['description']}</div>
                </a>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>"""
    
    with open('fsm_visualizations_index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("   ✓ Generated fsm_visualizations_index.html")


def main():
    """Main function."""
    print("=" * 70)
    print("🎨 FSM HTML Page Generator - ALL MODELS")
    print("=" * 70)
    print()
    print("This will generate simple HTML pages for all 16 models")
    print("(excluding Deed/DeedParticipant which already have detailed pages)")
    print()
    
    # Generate pages for all models
    total_pages = generate_all_models()
    
    # Generate master index
    generate_master_index()
    
    print()
    print("=" * 70)
    print(f"✅ Generation complete!")
    print()
    print(f"📊 Statistics:")
    print(f"   • Models processed: {len(MODELS_CONFIG)}")
    print(f"   • Total pages generated: {total_pages}")
    print(f"   • Directories created: {len(MODELS_CONFIG)}")
    print()
    print("📁 Output:")
    print("   • fsm_visualizations_index.html (master index)")
    print("   • 16 directories: [model]_visualization/")
    print()
    print("🌐 To view:")
    print("   1. Open fsm_visualizations_index.html")
    print("   2. Click on any model to explore its states")
    print("   3. Each state links to complete documentation")
    print()
    print("💡 Note: For fully detailed pages like Deeds, copy")
    print("   generate_deed_state_pages.py and adapt it.")
    print("=" * 70)


if __name__ == '__main__':
    main()

