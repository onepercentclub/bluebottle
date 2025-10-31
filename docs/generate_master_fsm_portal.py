#!/usr/bin/env python3
"""
Generate Master FSM Documentation Portal
Creates a comprehensive HTML portal for all 18 FSM models with navigation and search.
"""

import os

# Model definitions with metadata
MODELS = [
    {
        'category': 'Time-Based Activities',
        'models': [
            {
                'name': 'DateActivity',
                'description': 'Time-based activities with specific start dates and times',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
                'complexity': 'High',
                'markdown_section': '1',
            },
            {
                'name': 'DeadlineActivity',
                'description': 'Activities with registration and completion deadlines',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
                'complexity': 'High',
                'markdown_section': '2',
            },
            {
                'name': 'ScheduleActivity',
                'description': 'Activities with flexible scheduling slots',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
                'complexity': 'Very High',
                'markdown_section': '3',
            },
            {
                'name': 'PeriodicActivity',
                'description': 'Recurring activities that repeat on a schedule',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'full', 'succeeded', 'expired', 'cancelled', 'rejected'],
                'complexity': 'High',
                'markdown_section': '4',
            },
            {
                'name': 'RegisteredDateActivity',
                'description': 'Past activities registered retroactively',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'planned', 'succeeded', 'cancelled', 'rejected'],
                'complexity': 'Medium',
                'markdown_section': '5',
            },
        ]
    },
    {
        'category': 'Time-Based Participants',
        'models': [
            {
                'name': 'DateParticipant',
                'description': 'Participants for date-based activities',
                'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
                'complexity': 'High',
                'markdown_section': '6',
            },
            {
                'name': 'DeadlineParticipant',
                'description': 'Participants for deadline-based activities',
                'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
                'complexity': 'High',
                'markdown_section': '7',
            },
            {
                'name': 'ScheduleParticipant',
                'description': 'Participants assigned to schedule slots',
                'states': ['new', 'accepted', 'scheduled', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
                'complexity': 'Very High',
                'markdown_section': '8',
            },
            {
                'name': 'TeamScheduleParticipant',
                'description': 'Team members in scheduled activities',
                'states': ['new', 'accepted', 'scheduled', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
                'complexity': 'High',
                'markdown_section': '9',
            },
            {
                'name': 'PeriodicParticipant',
                'description': 'Participants in recurring activities',
                'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
                'complexity': 'Medium',
                'markdown_section': '10',
            },
            {
                'name': 'RegisteredDateParticipant',
                'description': 'Retroactively registered participants',
                'states': ['new', 'accepted', 'rejected', 'removed', 'withdrawn', 'cancelled', 'succeeded'],
                'complexity': 'Low',
                'markdown_section': '11',
            },
        ]
    },
    {
        'category': 'Funding',
        'models': [
            {
                'name': 'Funding',
                'description': 'Crowdfunding campaigns with financial goals',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'on_hold', 'succeeded', 'partially_funded', 'refunded', 'cancelled', 'rejected'],
                'complexity': 'High',
                'markdown_section': '12',
            },
            {
                'name': 'Donor',
                'description': 'Individual donations and donor management',
                'states': ['new', 'pending', 'succeeded', 'failed', 'refunded', 'activity_refunded', 'expired'],
                'complexity': 'Medium',
                'markdown_section': '13',
            },
            {
                'name': 'Payment',
                'description': 'Payment processing and transaction states',
                'states': ['new', 'pending', 'action_needed', 'succeeded', 'failed', 'refund_requested', 'refunded'],
                'complexity': 'Medium',
                'markdown_section': '14',
            },
        ]
    },
    {
        'category': 'Collect Activities',
        'models': [
            {
                'name': 'CollectActivity',
                'description': 'Collection activities for gathering items or pledges',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'succeeded', 'expired', 'cancelled', 'rejected'],
                'complexity': 'Medium',
                'markdown_section': '15',
            },
            {
                'name': 'CollectContributor',
                'description': 'Contributors to collection activities',
                'states': ['new', 'accepted', 'succeeded', 'failed', 'withdrawn', 'rejected'],
                'complexity': 'Medium',
                'markdown_section': '16',
            },
        ]
    },
    {
        'category': 'Deeds',
        'models': [
            {
                'name': 'Deed',
                'description': 'One-off volunteering activities',
                'states': ['draft', 'submitted', 'needs_work', 'open', 'succeeded', 'expired', 'cancelled', 'rejected', 'deleted'],
                'complexity': 'Medium',
                'markdown_section': '17',
                'has_html': True,
                'html_path': 'deed_states_visualization/index.html',
            },
            {
                'name': 'DeedParticipant',
                'description': 'Participants in deed activities',
                'states': ['new', 'accepted', 'rejected', 'withdrawn', 'succeeded', 'failed'],
                'complexity': 'Medium',
                'markdown_section': '18',
                'has_html': True,
                'html_path': 'deed_states_visualization/index.html',
            },
        ]
    },
]


def get_state_color(state_value):
    """Get color for state badge."""
    colors = {
        'draft': '#28a745', 'submitted': '#6c757d', 'needs_work': '#ffc107',
        'open': '#17a2b8', 'succeeded': '#28a745', 'failed': '#dc3545',
        'cancelled': '#6c757d', 'rejected': '#dc3545', 'expired': '#6c757d',
        'full': '#fd7e14', 'partially_funded': '#ffc107', 'refunded': '#6c757d',
        'accepted': '#17a2b8', 'withdrawn': '#6c757d', 'removed': '#dc3545',
        'new': '#17a2b8', 'pending': '#ffc107', 'scheduled': '#17a2b8',
        'on_hold': '#ffc107', 'activity_refunded': '#6c757d', 'planned': '#17a2b8',
    }
    return colors.get(state_value, '#007bff')


def get_complexity_color(complexity):
    """Get color for complexity badge."""
    colors = {
        'Low': '#28a745',
        'Medium': '#17a2b8',
        'High': '#ffc107',
        'Very High': '#dc3545',
    }
    return colors.get(complexity, '#6c757d')


def generate_portal():
    """Generate the master portal HTML."""
    
    # Count total models and states
    total_models = sum(len(cat['models']) for cat in MODELS)
    total_states = sum(len(model['states']) for cat in MODELS for model in cat['models'])
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bluebottle FSM Documentation Portal</title>
    <link rel="stylesheet" href="deed_states_visualization/state_styles.css">
    <style>
        .portal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            border-radius: 8px;
            margin-bottom: 40px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .portal-header h1 {
            color: white;
            margin: 0 0 15px 0;
            font-size: 42px;
        }
        .portal-header p {
            color: rgba(255,255,255,0.9);
            font-size: 18px;
            margin: 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e1e4e8;
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            display: block;
            margin-bottom: 8px;
        }
        .stat-label {
            font-size: 14px;
            color: #586069;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .quick-links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .quick-link-card {
            background: white;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            padding: 25px;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s;
        }
        .quick-link-card:hover {
            border-color: #667eea;
            transform: translateY(-3px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
        }
        .quick-link-card h3 {
            margin: 0 0 10px 0;
            color: #24292e;
            font-size: 20px;
        }
        .quick-link-card p {
            margin: 0;
            color: #586069;
            font-size: 14px;
        }
        .quick-link-icon {
            font-size: 32px;
            margin-bottom: 15px;
            display: block;
        }
        .model-card-enhanced {
            background: white;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        .model-card-enhanced:hover {
            border-color: #667eea;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.15);
        }
        .model-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        .model-title {
            font-size: 22px;
            font-weight: 600;
            color: #24292e;
            margin: 0;
        }
        .complexity-badge {
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            color: white;
            text-transform: uppercase;
        }
        .model-description {
            color: #586069;
            margin-bottom: 15px;
            line-height: 1.6;
        }
        .state-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }
        .state-badge-small {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            color: white;
            background: #6c757d;
        }
        .model-links {
            display: flex;
            gap: 15px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e1e4e8;
        }
        .model-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .model-link:hover {
            text-decoration: underline;
        }
        .search-box {
            width: 100%;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            margin-bottom: 30px;
            transition: border-color 0.3s;
        }
        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }
        .category-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            border-radius: 8px;
            margin: 40px 0 25px 0;
        }
        .category-header h2 {
            margin: 0;
            color: white;
            font-size: 28px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="portal-header">
            <h1>🔄 Bluebottle FSM Documentation Portal</h1>
            <p>Comprehensive documentation for all Finite State Machines</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">""" + str(total_models) + """</span>
                    <span class="stat-label">Models</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">""" + str(len(MODELS)) + """</span>
                    <span class="stat-label">Categories</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">""" + str(total_states) + """</span>
                    <span class="stat-label">Total States</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">100%</span>
                    <span class="stat-label">Coverage</span>
                </div>
            </div>
        </header>
        
        <div class="quick-links">
            <a href="FSM_COMPLETE_DOCUMENTATION.md" class="quick-link-card">
                <span class="quick-link-icon">📚</span>
                <h3>Complete Documentation</h3>
                <p>All 18 models with states, transitions, triggers, and effects</p>
            </a>
            <a href="FSM_QUICK_START.md" class="quick-link-card">
                <span class="quick-link-icon">⚡</span>
                <h3>Quick Start Guide</h3>
                <p>Get started in 5 minutes with examples and common queries</p>
            </a>
            <a href="deed_states_visualization/index.html" class="quick-link-card">
                <span class="quick-link-icon">🎨</span>
                <h3>Interactive Demo</h3>
                <p>Explore Deed states with clickable transitions</p>
            </a>
            <a href="FSM_DOCUMENTATION_SUMMARY.md" class="quick-link-card">
                <span class="quick-link-icon">📊</span>
                <h3>Project Summary</h3>
                <p>Overview, statistics, and maintenance guide</p>
            </a>
        </div>
        
        <input type="text" class="search-box" id="searchBox" placeholder="🔍 Search models (e.g., 'funding', 'participant', 'deadline')..." onkeyup="filterModels()">
"""
    
    # Generate model cards for each category
    for category_data in MODELS:
        category = category_data['category']
        models = category_data['models']
        
        html += f"""
        <div class="category-header">
            <h2>{category}</h2>
        </div>
"""
        
        for model in models:
            complexity_color = get_complexity_color(model['complexity'])
            
            html += f"""
        <div class="model-card-enhanced" data-search="{model['name'].lower()} {model['description'].lower()} {category.lower()}">
            <div class="model-header">
                <h3 class="model-title">{model['name']}</h3>
                <span class="complexity-badge" style="background-color: {complexity_color};">{model['complexity']}</span>
            </div>
            <p class="model-description">{model['description']}</p>
            
            <div class="state-badges">
"""
            
            # Show first 8 states
            for state in model['states'][:8]:
                color = get_state_color(state)
                html += f"""                <span class="state-badge-small" style="background-color: {color};">{state}</span>
"""
            
            if len(model['states']) > 8:
                html += f"""                <span class="state-badge-small" style="background-color: #6c757d;">+{len(model['states']) - 8} more</span>
"""
            
            html += f"""            </div>
            
            <div class="model-links">
                <a href="FSM_COMPLETE_DOCUMENTATION.md#{model['markdown_section']}-{model['name'].lower()}" class="model-link">
                    📖 View Documentation
                </a>
"""
            
            if model.get('has_html'):
                html += f"""                <a href="{model['html_path']}" class="model-link">
                    🌐 Interactive HTML
                </a>
"""
            
            html += """            </div>
        </div>
"""
    
    html += """
    </div>
    
    <script>
        function filterModels() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const modelCards = document.querySelectorAll('[data-search]');
            
            modelCards.forEach(card => {
                const searchText = card.getAttribute('data-search');
                if (searchText.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>"""
    
    # Write file
    with open('fsm_documentation_portal.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Generated: fsm_documentation_portal.html")


def main():
    """Main function."""
    print("=" * 70)
    print("🚀 Generating Master FSM Documentation Portal")
    print("=" * 70)
    print()
    
    generate_portal()
    
    print()
    print("=" * 70)
    print("✅ Portal generation complete!")
    print()
    print("📁 Output: fsm_documentation_portal.html")
    print("🌐 Open in browser to explore all 18 FSM models")
    print()
    print("Features:")
    print("  • Search functionality")
    print("  • Quick links to all docs")
    print("  • Visual model cards")
    print("  • Complexity indicators")
    print("  • Direct links to markdown sections")
    print("=" * 70)


if __name__ == '__main__':
    main()

