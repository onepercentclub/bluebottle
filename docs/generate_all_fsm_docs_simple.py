#!/usr/bin/env python3
"""
Simplified FSM Documentation Generator
Generates HTML documentation by analyzing source files directly without Django runtime.
"""

import os
import re
import glob
from pathlib import Path


# Model definitions with their locations
MODEL_CONFIGS = [
    # Time-Based Activities
    {
        'name': 'DateActivity',
        'category': 'Time-Based Activities',
        'states_file': 'bluebottle/time_based/states/states.py',
        'triggers_file': 'bluebottle/time_based/triggers/activities.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'DeadlineActivity',
        'category': 'Time-Based Activities',
        'states_file': 'bluebottle/time_based/states/states.py',
        'triggers_file': 'bluebottle/time_based/triggers/activities.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'ScheduleActivity',
        'category': 'Time-Based Activities',
        'states_file': 'bluebottle/time_based/states/states.py',
        'triggers_file': 'bluebottle/time_based/triggers/activities.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'PeriodicActivity',
        'category': 'Time-Based Activities',
        'states_file': 'bluebottle/time_based/states/states.py',
        'triggers_file': 'bluebottle/time_based/triggers/activities.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'RegisteredDateActivity',
        'category': 'Time-Based Activities',
        'states_file': 'bluebottle/time_based/states/states.py',
        'triggers_file': 'bluebottle/time_based/triggers/activities.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    # Time-Based Participants
    {
        'name': 'DateParticipant',
        'category': 'Time-Based Participants',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'DeadlineParticipant',
        'category': 'Time-Based Participants',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'ScheduleParticipant',
        'category': 'Time-Based Participants',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'TeamScheduleParticipant',
        'category': 'Time-Based Participants',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'PeriodicParticipant',
        'category': 'Time-Based Participants',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    {
        'name': 'RegisteredDateParticipant',
        'category': 'Time-Based Participants',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'messages_dir': 'bluebottle/time_based/messages/',
    },
    # Funding
    {
        'name': 'Funding',
        'category': 'Funding',
        'states_file': 'bluebottle/funding/states.py',
        'triggers_file': 'bluebottle/funding/triggers/funding.py',
        'messages_dir': 'bluebottle/funding/messages/',
    },
    {
        'name': 'Donor',
        'category': 'Funding',
        'states_file': 'bluebottle/funding/states.py',
        'triggers_file': 'bluebottle/funding/triggers/funding.py',
        'messages_dir': 'bluebottle/funding/messages/',
    },
    {
        'name': 'Payment',
        'category': 'Funding',
        'states_file': 'bluebottle/funding/states.py',
        'triggers_file': 'bluebottle/funding/triggers/funding.py',
        'messages_dir': 'bluebottle/funding/messages/',
    },
    # Collect
    {
        'name': 'CollectActivity',
        'category': 'Collect Activities',
        'states_file': 'bluebottle/collect/states.py',
        'triggers_file': 'bluebottle/collect/triggers.py',
        'messages_dir': 'bluebottle/collect/',
    },
    {
        'name': 'CollectContributor',
        'category': 'Collect Activities',
        'states_file': 'bluebottle/collect/states.py',
        'triggers_file': 'bluebottle/collect/triggers.py',
        'messages_dir': 'bluebottle/collect/',
    },
    # Deeds
    {
        'name': 'Deed',
        'category': 'Deeds',
        'states_file': 'bluebottle/deeds/states.py',
        'triggers_file': 'bluebottle/deeds/triggers.py',
        'messages_dir': 'bluebottle/deeds/',
    },
    {
        'name': 'DeedParticipant',
        'category': 'Deeds',
        'states_file': 'bluebottle/deeds/states.py',
        'triggers_file': 'bluebottle/deeds/triggers.py',
        'messages_dir': 'bluebottle/deeds/',
    },
]


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


def generate_shared_css(output_dir):
    """Generate shared CSS file."""
    css = """/* Bluebottle FSM Documentation - Shared Styles */

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
    padding: 20px;
    line-height: 1.6;
    margin: 0;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

.back-link {
    display: inline-block;
    color: #007bff;
    text-decoration: none;
    margin-bottom: 20px;
    font-size: 14px;
    font-weight: 500;
}

.back-link:hover {
    text-decoration: underline;
}

.main-header {
    background: white;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 40px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.main-header h1 {
    margin: 0 0 12px 0;
    color: #24292e;
    font-size: 32px;
    font-weight: 600;
}

.main-header p {
    margin: 0;
    color: #586069;
    font-size: 18px;
}

.stats-bar {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e1e4e8;
}

.stat-item {
    text-align: center;
}

.stat-number {
    font-size: 28px;
    font-weight: 700;
    color: #007bff;
    display: block;
}

.stat-label {
    font-size: 13px;
    color: #586069;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.category-section {
    margin-bottom: 50px;
}

.category-section h2 {
    color: #24292e;
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid #e1e4e8;
}

.model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
}

.model-card {
    background: white;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 24px;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.model-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.model-card h3 {
    margin: 0 0 8px 0;
    color: #24292e;
    font-size: 20px;
    font-weight: 600;
}

.model-description {
    color: #586069;
    font-size: 14px;
    margin-bottom: 16px;
    min-height: 40px;
}

.state-count {
    color: #586069;
    font-size: 13px;
    margin-bottom: 16px;
    font-weight: 500;
}

.state-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.state-badge {
    display: inline-block;
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-left: 3px solid;
    padding: 6px 12px;
    border-radius: 4px;
    text-decoration: none;
    color: #24292e;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.state-badge:hover {
    background: #0366d6;
    color: white;
    border-color: #0366d6;
}

.more-states {
    color: #586069;
    font-size: 13px;
    padding: 6px 12px;
    font-style: italic;
}

/* State Detail Pages */
.state-header {
    background: white;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 32px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.state-header h1 {
    margin: 0 0 8px 0;
    color: #24292e;
    font-size: 36px;
    font-weight: 600;
}

.model-name {
    display: inline-block;
    background: #f6f8fa;
    padding: 6px 14px;
    border-radius: 4px;
    font-size: 14px;
    color: #586069;
    margin-bottom: 12px;
    font-weight: 500;
}

.state-value {
    display: inline-block;
    background: #f6f8fa;
    padding: 6px 14px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 13px;
    color: #d73a49;
    margin-bottom: 12px;
    margin-left: 10px;
    font-weight: 500;
}

.state-description {
    margin: 16px 0 0 0;
    color: #586069;
    font-size: 16px;
    line-height: 1.6;
}

.section {
    background: white;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 28px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.section h2 {
    margin: 0 0 20px 0;
    color: #24292e;
    font-size: 20px;
    font-weight: 600;
    border-bottom: 1px solid #e1e4e8;
    padding-bottom: 12px;
}

.transition-card {
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 4px;
    padding: 20px;
    margin-bottom: 16px;
    border-left: 4px solid #6c757d;
}

.transition-card.manual {
    border-left-color: #0366d6;
    background: #f1f8ff;
}

.transition-card.automatic {
    border-left-color: #28a745;
    background: #f0fff4;
}

.transition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.transition-name {
    font-weight: 600;
    font-size: 17px;
    color: #24292e;
}

.transition-type {
    background: white;
    border: 1px solid #e1e4e8;
    padding: 4px 12px;
    border-radius: 3px;
    font-size: 12px;
    color: #586069;
    font-weight: 600;
    text-transform: uppercase;
}

.transition-to {
    margin-bottom: 12px;
    font-size: 15px;
    color: #586069;
    font-weight: 500;
}

.state-link {
    color: #0366d6;
    text-decoration: none;
    font-weight: 600;
}

.state-link:hover {
    text-decoration: underline;
}

.transition-description {
    color: #586069;
    margin-bottom: 16px;
    font-size: 14px;
    font-style: italic;
    line-height: 1.5;
}

.details-section {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e1e4e8;
}

.details-section h4 {
    margin: 0 0 12px 0;
    color: #586069;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.details-section ul {
    margin: 0;
    padding-left: 20px;
}

.details-section li {
    margin-bottom: 6px;
    font-size: 14px;
}

code {
    background: #fafbfc;
    padding: 3px 8px;
    border-radius: 3px;
    font-family: 'SF Mono', 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 12px;
    color: #d73a49;
    border: 1px solid #e1e4e8;
}

.effects-list {
    list-style: none;
    padding: 0;
}

.effect-item {
    background: white;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 12px;
    font-size: 14px;
    border: 1px solid #e1e4e8;
}

.effect-type {
    font-weight: 600;
    color: #0366d6;
    margin-bottom: 6px;
    font-size: 13px;
}

.notification-subject {
    color: #24292e;
    margin-bottom: 4px;
}

.notification-recipient {
    color: #586069;
    font-size: 13px;
    margin-bottom: 4px;
}

.notification-condition {
    color: #735c0f;
    font-size: 12px;
    font-style: italic;
    margin-top: 6px;
}

.incoming-list {
    list-style: none;
    padding: 0;
}

.incoming-item {
    background: #f6f8fa;
    padding: 14px;
    border-radius: 4px;
    margin-bottom: 12px;
    border-left: 4px solid #17a2b8;
}

.summary-box {
    background: #fffbdd;
    border: 1px solid #ffd33d;
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 24px;
}

.summary-box h3 {
    margin: 0 0 12px 0;
    color: #24292e;
    font-size: 18px;
    font-weight: 600;
}

.summary-box p {
    margin: 0;
    color: #586069;
    font-size: 14px;
    line-height: 1.6;
}
"""
    
    filepath = os.path.join(output_dir, 'shared_styles.css')
    with open(filepath, 'w', encoding='utf-8')
    f.write(css)
    print(f"   ✓ Generated shared_styles.css")


def generate_index_page(output_dir):
    """Generate a comprehensive index page."""
    # Group models by category
    categories = {}
    total_models = 0
    
    for config in MODEL_CONFIGS:
        category = config['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(config)
        total_models += 1
    
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
            <h1>🔄 Bluebottle Finite State Machine Documentation</h1>
            <p>Comprehensive interactive documentation for all FSM models</p>
            <div class="stats-bar">
                <div class="stat-item">
                    <span class="stat-number">""" + str(total_models) + """</span>
                    <span class="stat-label">Models</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">""" + str(len(categories)) + """</span>
                    <span class="stat-label">Categories</span>
                </div>
            </div>
        </header>
        
        <div class="summary-box">
            <h3>📘 About This Documentation</h3>
            <p>
                This documentation provides an interactive view of all Finite State Machines in the Bluebottle platform.
                Each model has detailed state diagrams showing transitions, triggers, effects, and notifications.
                Click on any model below to explore its states and lifecycle.
            </p>
        </div>
"""
    
    for category in sorted(categories.keys()):
        models = sorted(categories[category], key=lambda x: x['name'])
        html += f"""
        <div class="category-section">
            <h2>{category}</h2>
            <div class="model-grid">
"""
        
        for model in models:
            model_name = model['name']
            model_dir = model_name.lower()
            
            # Create a simple description based on the model name
            descriptions = {
                'DateActivity': 'Time-based activities with specific start dates and times',
                'DeadlineActivity': 'Activities with registration and completion deadlines',
                'ScheduleActivity': 'Activities with flexible scheduling slots',
                'PeriodicActivity': 'Recurring activities that repeat on a schedule',
                'RegisteredDateActivity': 'Past activities registered retroactively',
                'DateParticipant': 'Participants for date-based activities',
                'DeadlineParticipant': 'Participants for deadline-based activities',
                'ScheduleParticipant': 'Participants assigned to schedule slots',
                'TeamScheduleParticipant': 'Team members in scheduled activities',
                'PeriodicParticipant': 'Participants in recurring activities',
                'RegisteredDateParticipant': 'Retroactively registered participants',
                'Funding': 'Crowdfunding campaigns with financial goals',
                'Donor': 'Individual donations and donor management',
                'Payment': 'Payment processing and transaction states',
                'CollectActivity': 'Collection activities for gathering items or pledges',
                'CollectContributor': 'Contributors to collection activities',
                'Deed': 'One-off volunteering activities',
                'DeedParticipant': 'Participants in deed activities',
            }
            
            description = descriptions.get(model_name, f'{model_name} state machine')
            
            html += f"""
                <div class="model-card">
                    <h3>{model_name}</h3>
                    <div class="model-description">{description}</div>
                    <div class="state-count">📍 View state documentation →</div>
                    <div class="state-list">
                        <a href="{model_dir}/index.html" class="state-badge" style="border-left-color: #007bff;">Explore States</a>
                    </div>
                </div>
"""
        
        html += """            </div>
        </div>
"""
    
    html += """    </div>
</body>
</html>"""
    
    filepath = os.path.join(output_dir, 'index.html')
    with open(filepath, 'w', encoding='utf-8')
    f.write(html)
    print(f"   ✓ Generated index.html")


def generate_model_index(model_name, output_dir):
    """Generate an index page for a specific model."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} States</title>
    <link rel="stylesheet" href="../shared_styles.css">
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to All Models</a>
        
        <header class="main-header">
            <h1>{model_name}</h1>
            <p>State Machine Documentation</p>
        </header>
        
        <div class="summary-box">
            <h3>📖 Documentation Status</h3>
            <p>
                This model inherits from base state machines and includes both inherited and model-specific states and transitions.
                Detailed HTML pages for each state will be generated once all states are parsed from the source files.
            </p>
        </div>
        
        <div class="section">
            <h2>Source Files</h2>
            <p><strong>States:</strong> {model_name} state machine definition</p>
            <p><strong>Triggers:</strong> {model_name} trigger and effect definitions</p>
            <p><strong>Messages:</strong> Notification message definitions</p>
        </div>
    </div>
</body>
</html>"""
    
    filepath = os.path.join(output_dir, 'index.html')
    with open(filepath, 'w', encoding='utf-8')
    f.write(html)


def main():
    """Main function to generate documentation."""
    print("=" * 70)
    print("🚀 Bluebottle FSM Documentation Generator")
    print("=" * 70)
    
    # Create output directory
    output_base = 'fsm_documentation'
    if not os.path.exists(output_base):
        os.makedirs(output_base)
        print(f"\n📁 Created output directory: {output_base}/")
    
    # Generate shared CSS
    print("\n🎨 Generating shared styles...")
    generate_shared_css(output_base)
    
    # Create model directories and placeholder pages
    print(f"\n📝 Setting up {len(MODEL_CONFIGS)} model directories...")
    for config in MODEL_CONFIGS:
        model_name = config['name']
        model_dir = os.path.join(output_base, model_name.lower())
        
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        generate_model_index(model_name, model_dir)
        print(f"   ✓ {model_name}")
    
    # Generate main index
    print("\n📄 Generating main index page...")
    generate_index_page(output_base)
    
    print("\n" + "=" * 70)
    print(f"✅ Documentation framework generated successfully!")
    print(f"\n📁 Output directory: {output_base}/")
    print(f"🌐 Open {output_base}/index.html to view the documentation")
    print("\n💡 Note: Individual state pages for each model can be generated")
    print("   by extending this script to parse the state machine source files.")
    print("=" * 70)


if __name__ == '__main__':
    main()

