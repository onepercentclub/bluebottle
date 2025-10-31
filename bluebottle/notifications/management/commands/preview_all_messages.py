"""
Django management command to preview all email messages.

Comprehensive email message preview generator for ALL TransitionMessage classes.

This command discovers and generates previews for all email notifications across:
- Activities (activity_manager, participant, reviewer, matching)
- Time-based (participants, teams, registrations, slots)
- Funding (donations, campaigns)  
- Grant Management
- Initiatives
- Deeds & Collect activities
- Updates
- Members

Usage:
    python manage.py preview_all_messages --list-modules
    python manage.py preview_all_messages --module activities
    python manage.py preview_all_messages --all
    python manage.py preview_all_messages --all --all-languages
"""
import os
import json
import importlib
import inspect
import re
import ast

from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import loader
from django.utils import translation
from django.db import connection
from bluebottle.notifications.messages import TransitionMessage
from bluebottle.clients.models import Client

# Import all message modules
MESSAGE_MODULES = {
    'activities.activity_manager': 'bluebottle.activities.messages.activity_manager',
    'activities.participant': 'bluebottle.activities.messages.participant',
    'activities.reviewer': 'bluebottle.activities.messages.reviewer',
    'activities.matching': 'bluebottle.activities.messages.matching',
    
    'time_based.messages': 'bluebottle.time_based.messages.messages',
    'time_based.participants': 'bluebottle.time_based.messages.participants',
    'time_based.teams': 'bluebottle.time_based.messages.teams',
    'time_based.registrations': 'bluebottle.time_based.messages.registrations',
    
    'funding.contributor': 'bluebottle.funding.messages.funding.contributor',
    'funding.activity_manager': 'bluebottle.funding.messages.funding.activity_manager',
    'funding.platform_manager': 'bluebottle.funding.messages.funding.platform_manager',
    
    'grant_management.activity_manager': 'bluebottle.grant_management.messages.activity_manager',
    'grant_management.grant_provider': 'bluebottle.grant_management.messages.grant_provider',
    
    'initiatives.initiator': 'bluebottle.initiatives.messages.initiator',
    'initiatives.reviewer': 'bluebottle.initiatives.messages.reviewer',
    
    'deeds': 'bluebottle.deeds.messages',
    'collect': 'bluebottle.collect.messages',
    'updates': 'bluebottle.updates.messages',
    'members': 'bluebottle.members.messages',
}

# Trigger file paths for analyzing transitions
TRIGGER_MODULES = [
    'bluebottle.activities.triggers',
    'bluebottle.initiatives.triggers',
    'bluebottle.funding.triggers.funding',
    'bluebottle.deeds.triggers',
    'bluebottle.collect.triggers',
    'bluebottle.time_based.triggers.participants',
    'bluebottle.time_based.triggers.registrations',
    'bluebottle.time_based.triggers.slots',
    'bluebottle.time_based.triggers.teams',
    'bluebottle.time_based.triggers.contributions',
    'bluebottle.time_based.triggers.activities',
    'bluebottle.grant_management.triggers',
]


def analyze_triggers():
    """
    Analyze all trigger files to build a mapping of messages to their triggering transitions.
    
    Returns:
        dict: Mapping of message class names to lists of trigger info dicts
    """
    message_triggers = {}
    
    for trigger_module_path in TRIGGER_MODULES:
        try:
            module = importlib.import_module(trigger_module_path)
            
            # Get the source file path
            if not hasattr(module, '__file__'):
                continue
                
            source_file = module.__file__
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse to find NotificationEffect calls
            trigger_pattern = r'TransitionTrigger\s*\(\s*([^,]+),\s*effects=\[(.*?)\]'
            
            # Find all trigger blocks
            trigger_matches = re.finditer(trigger_pattern, source_code, re.DOTALL)
            
            for match in trigger_matches:
                transition_ref = match.group(1).strip()
                effects_block = match.group(2)
                
                # Extract transition name (e.g., "ActivityStateMachine.submit" -> "submit")
                transition_parts = transition_ref.split('.')
                if len(transition_parts) >= 2:
                    state_machine = transition_parts[0]
                    transition_name = transition_parts[-1]
                else:
                    transition_name = transition_ref
                    state_machine = "Unknown"
                
                # Find NotificationEffect entries
                notification_pattern = r'NotificationEffect\s*\(\s*([^,\)]+)'
                notification_matches = re.finditer(notification_pattern, effects_block)
                
                for notif_match in notification_matches:
                    message_class_name = notif_match.group(1).strip()
                    
                    # Extract conditions if present
                    # Look for conditions= near this NotificationEffect
                    effect_start = notif_match.start()
                    effect_context = effects_block[max(0, effect_start-50):effect_start+200]
                    
                    conditions = []
                    conditions_match = re.search(r'conditions=\[(.*?)\]', effect_context, re.DOTALL)
                    if conditions_match:
                        cond_text = conditions_match.group(1)
                        # Extract condition function names
                        cond_funcs = re.findall(r'(\w+)', cond_text)
                        conditions = [c for c in cond_funcs if not c in ['conditions', 'True', 'False']]
                    
                    # Build trigger info
                    trigger_info = {
                        'transition': transition_name,
                        'state_machine': state_machine,
                        'module': trigger_module_path.split('.')[-1],  # e.g., 'triggers', 'participants'
                        'full_module': trigger_module_path,
                        'conditions': conditions
                    }
                    
                    if message_class_name not in message_triggers:
                        message_triggers[message_class_name] = []
                    
                    message_triggers[message_class_name].append(trigger_info)
            
            # Also look for ModelChangedTrigger
            model_changed_pattern = r'ModelChangedTrigger\s*\(\s*[\'"]?([^,\'"]+)[\'"]?,\s*effects=\[(.*?)\]'
            model_matches = re.finditer(model_changed_pattern, source_code, re.DOTALL)
            
            for match in model_matches:
                field_name = match.group(1).strip().strip('"\'')
                effects_block = match.group(2)
                
                # Find NotificationEffect entries
                notification_matches = re.finditer(notification_pattern, effects_block)
                
                for notif_match in notification_matches:
                    message_class_name = notif_match.group(1).strip()
                    
                    trigger_info = {
                        'transition': f'field_changed:{field_name}',
                        'state_machine': 'ModelChanged',
                        'module': trigger_module_path.split('.')[-1],
                        'full_module': trigger_module_path,
                        'conditions': []
                    }
                    
                    if message_class_name not in message_triggers:
                        message_triggers[message_class_name] = []
                    
                    message_triggers[message_class_name].append(trigger_info)
                    
        except Exception as e:
            print(f"Warning: Could not analyze {trigger_module_path}: {e}")
            continue
    
    return message_triggers


def format_trigger_description(triggers):
    """
    Format trigger information into a human-readable description.
    
    Args:
        triggers: List of trigger info dicts
        
    Returns:
        str: HTML-formatted trigger description
    """
    if not triggers:
        return ""
    
    descriptions = []
    
    # Group by state machine
    by_machine = {}
    for trigger in triggers:
        machine = trigger['state_machine']
        if machine not in by_machine:
            by_machine[machine] = []
        by_machine[machine].append(trigger)
    
    for machine, machine_triggers in sorted(by_machine.items()):
        transitions = []
        for t in machine_triggers:
            trans_desc = f"<code>{t['transition']}</code>"
            if t['conditions']:
                cond_list = ', '.join([f'<code>{c}</code>' for c in t['conditions'][:3]])
                if len(t['conditions']) > 3:
                    cond_list += ', ...'
                trans_desc += f" <small>(when: {cond_list})</small>"
            transitions.append(trans_desc)
        
        machine_desc = f"<strong>{machine}</strong>: {', '.join(transitions)}"
        descriptions.append(machine_desc)
    
    return "<br>".join(descriptions)


#  Mock objects for different entity types
class MockMember:
    """Mock Member/User object"""
    def __init__(self, language='en'):
        self.id = 1
        self.first_name = "Jane"
        self.last_name = "Doe"
        self.short_name = "Jane D."
        self.full_name = "Jane Doe"
        self.email = "jane.doe@example.com"
        self.primary_language = language

class MockActivity:
    """Mock Activity object"""
    def __init__(self, language='en'):
        self.id = 123
        self.title = "Clean up the local park"
        self.slug = "clean-up-the-local-park"
        self.description = "Help us clean the local park!"
        self.status = "open"
        self.owner = MockMember(language)
        self.organization = None
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/activities/details/deed/{self.id}/{self.slug}"

class MockParticipant:
    """Mock Participant object"""
    def __init__(self, language='en'):
        self.id = 456
        self.user = MockMember(language)
        self.activity = MockActivity(language)
        self.status = "accepted"
        self.motivation = "I love helping the community!"
        self.time_spent = None
        
    @property
    def owner(self):
        return self.user
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/activities/participants/{self.id}"

class MockSlot:
    """Mock Activity Slot object"""
    def __init__(self, language='en'):
        self.id = 789
        self.title = "Morning Shift"
        self.activity = MockActivity(language)
        self.start = None
        self.duration = None
        self.capacity = 10
        
    @property
    def owner(self):
        return self.activity.owner
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/activities/slots/{self.id}"

class MockTeam:
    """Mock Team object"""
    def __init__(self, language='en'):
        self.id = 321
        self.name = "Team Awesome"
        self.activity = MockActivity(language)
        self.owner = MockMember(language)
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/activities/teams/{self.id}"

class MockFunding:
    """Mock Funding/Campaign object"""
    def __init__(self, language='en'):
        self.id = 111
        self.title = "Support our community garden"
        self.slug = "support-community-garden"
        self.target = 5000
        self.amount_raised = 3200
        self.owner = MockMember(language)
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/initiatives/activities/funding/{self.id}/{self.slug}"

class MockDonation:
    """Mock Donation object"""
    def __init__(self, language='en'):
        self.id = 222
        self.amount = 50
        self.user = MockMember(language)
        self.activity = MockFunding(language)
        
    @property
    def owner(self):
        return self.user
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/donations/{self.id}"

class MockInitiative:
    """Mock Initiative object"""
    def __init__(self, language='en'):
        self.id = 333
        self.title = "Green City Initiative"
        self.slug = "green-city-initiative"
        self.owner = MockMember(language)
        
    def get_absolute_url(self):
        return f"https://example.goodup.com/en/initiatives/{self.id}/{self.slug}"

class MockUpdate:
    """Mock Update/News post object"""
    def __init__(self, language='en'):
        self.id = 444
        self.title = "Great progress update!"
        self.message = "We've made amazing progress..."
        self.author = MockMember(language)
        self.activity = MockActivity(language)
        
    @property
    def owner(self):
        return self.author

# Mapping of message classes to appropriate mock objects
MOCK_OBJECT_MAP = {
    'Participant': MockParticipant,
    'Team': MockTeam,
    'Slot': MockSlot,
    'Funding': MockFunding,
    'Donation': MockDonation,
    'Donor': MockDonation,
    'Initiative': MockInitiative,
    'Update': MockUpdate,
    'Activity': MockActivity,
    'Member': MockMember,
}

def get_mock_object_for_message(message_class, language='en'):
    """Determine appropriate mock object based on message class name"""
    class_name = message_class.__name__
    
    # Try to match by class name patterns
    for key, mock_class in MOCK_OBJECT_MAP.items():
        if key.lower() in class_name.lower():
            return mock_class(language)
    
    # Default to Activity
    return MockActivity(language)

def discover_message_classes(module_path):
    """Discover all TransitionMessage subclasses in a module"""
    try:
        module = importlib.import_module(module_path)
        message_classes = []
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, TransitionMessage) and 
                obj != TransitionMessage and
                obj.__module__ == module_path):
                # Skip abstract message classes (only if Meta is defined on this class itself)
                # Check if this class defines its own Meta (not inherited)
                if 'Meta' in obj.__dict__:
                    # This class defines its own Meta, check if it's abstract
                    if hasattr(obj.Meta, 'abstract') and obj.Meta.abstract:
                        continue
                message_classes.append((name, obj))
        
        return sorted(message_classes)
    except ImportError as e:
        print(f"Warning: Could not import {module_path}: {e}")
        return []

def preview_message(message_class_name, message_class, language='en', output_format='html'):
    """Generate preview for a single message"""
    print(f"\n{'='*80}")
    print(f"Message: {message_class_name} ({language.upper()})")
    print(f"{'='*80}\n")
    
    # Get appropriate mock object
    mock_obj = get_mock_object_for_message(message_class, language)
    
    # Create message instance
    try:
        message_instance = message_class(mock_obj)
    except Exception as e:
        print(f"❌ Could not instantiate {message_class_name}: {e}")
        return None
    
    # Get mock recipient
    mock_recipient = MockMember(language)
    mock_recipient.primary_language = language
    
    try:
        with translation.override(language):
            # Force Django to load translations
            from django.utils.translation import get_language, gettext
            _ = gettext('test')

            if output_format == 'subject':
                context = message_instance.get_context(mock_recipient)
                subject = str(message_instance.subject.format(**context))
                print(f"Subject: {subject}\n")
                return subject
            
            elif output_format == 'html':
                html_content = message_instance.get_content_html(mock_recipient)
                context = message_instance.get_context(mock_recipient)
                subject = str(message_instance.subject.format(**context))
                
                print(f"Subject: {subject}")
                print(f"Template: mails/{message_instance.template}.html")
                print(f"HTML length: {len(html_content)} characters")
                return {'html': html_content, 'subject': subject, 'context': context}
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_preview(message_class_name, content, output_dir, module_name, language='en'):
    """Save preview to file with module organization"""
    if not content:
        return None
        
    # Create module subdirectory
    module_dir = os.path.join(output_dir, module_name.replace('.', '_'))
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)
    
    # Always include language suffix for consistency
    filename = f"{message_class_name}_{language}.html"
    filepath = os.path.join(module_dir, filename)
    
    html_content = content if isinstance(content, str) else content.get('html', '')
    
    # Extract subject if available
    subject = content.get('subject', '') if isinstance(content, dict) else ''
    
    # Wrap if needed
    if not html_content.strip().startswith('<!DOCTYPE'):
        subject_html = f'<h2 class="email-subject">{subject}</h2>' if subject else ''
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{message_class_name}</title>
</head>
<body>
    <div style="max-width: 800px; margin: 40px auto; padding: 20px;">
        <h2>{message_class_name}</h2>
        {subject_html}
        <p>Module: {module_name} | Language: {language.upper()}</p>
        <hr>
        {html_content}
    </div>
</body>
</html>"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Saved: {filepath}")
    
    # Return filepath and subject as a dict
    return {'filepath': filepath, 'subject': subject}

def generate_index(output_dir, all_messages, languages, trigger_map=None):
    """Generate comprehensive index page for all messages with modal support"""
    # Count by module
    module_counts = {}
    for module, messages in all_messages.items():
        module_counts[module] = len(messages)
    
    total_messages = sum(module_counts.values())
    
    # Generate metadata for modals
    metadata = {
        'languages': languages,
        'modules': {}
    }
    for module_name, messages in all_messages.items():
        module_dir = module_name.replace('.', '_')
        metadata['modules'][module_name] = {
            'directory': module_dir,
            'messages': []
        }
        for msg_name, msg_class in messages:
            # Get trigger information for this message
            triggers = trigger_map.get(msg_name, []) if trigger_map else []
            trigger_desc = format_trigger_description(triggers) if triggers else ""
            
            msg_data = {
                'name': msg_name,
                'description': (msg_class.__doc__ or "").strip().replace('\n', ' '),
                'triggers': triggers,
                'trigger_description': trigger_desc,
                'previews': {},
                'subjects': {}
            }
            for lang in languages:
                filename = f"{msg_name}_{lang}.html"
                filepath = f"{module_dir}/{filename}"
                full_path = os.path.join(output_dir, filepath)
                if os.path.exists(full_path):
                    msg_data['previews'][lang] = filepath
                    # Try to get subject from a subjects cache file
                    subject_cache_file = os.path.join(output_dir, '.subjects_cache.json')
                    try:
                        if os.path.exists(subject_cache_file):
                            with open(subject_cache_file, 'r', encoding='utf-8') as f:
                                subjects_cache = json.load(f)
                                cache_key = f"{module_name}:{msg_name}:{lang}"
                                if cache_key in subjects_cache:
                                    msg_data['subjects'][lang] = subjects_cache[cache_key]
                    except Exception:
                        pass
            metadata['modules'][module_name]['messages'].append(msg_data)
    
    # Save metadata as JSON
    metadata_path = os.path.join(output_dir, 'metadata_all.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Email Message Previews</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }}
        header h1 {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px 30px;
            border-radius: 12px;
            color: white;
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: 700;
            display: block;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .module-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .module-section h2 {{
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .message-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .message-item {{
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .message-name {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 14px;
        }}
        .message-description {{
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.4;
        }}
        .message-triggers {{
            font-size: 11px;
            color: #888;
            margin-bottom: 10px;
            padding: 8px;
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            border-radius: 3px;
            line-height: 1.5;
        }}
        .message-triggers strong {{
            color: #667eea;
        }}
        .message-triggers code {{
            background: #e9ecef;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 10px;
        }}
        .lang-links {{
            display: flex;
            gap: 8px;
        }}
        .lang-btn {{
            padding: 6px 14px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .lang-btn:hover {{
            background: #764ba2;
            transform: scale(1.05);
        }}
        
        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.8);
            animation: fadeIn 0.3s;
        }}
        .modal.active {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        .modal-content {{
            background-color: white;
            margin: 20px;
            padding: 0;
            border-radius: 12px;
            max-width: 900px;
            width: 100%;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            animation: slideIn 0.3s;
        }}
        @keyframes slideIn {{
            from {{
                transform: translateY(-50px);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
        .modal-header {{
            padding: 20px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .modal-header h2 {{
            margin: 0;
            font-size: 20px;
        }}
        .modal-controls {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .modal-lang-btn {{
            padding: 5px 12px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            text-transform: uppercase;
        }}
        .modal-lang-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        .modal-lang-btn.active {{
            background: white;
            color: #667eea;
        }}
        .close {{
            color: white;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
            padding: 0 10px;
            transition: all 0.2s;
        }}
        .close:hover {{
            transform: scale(1.2);
        }}
        .modal-subject {{
            padding: 15px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
            font-size: 16px;
            font-weight: 600;
            color: #495057;
            font-style: italic;
        }}
        .modal-subject:empty {{
            display: none;
        }}
        .modal-triggers-section {{
            padding: 15px 30px;
            background: #fff8e1;
            border-bottom: 2px solid #ffc107;
            font-size: 13px;
            color: #495057;
            line-height: 1.6;
        }}
        .modal-triggers-section:empty {{
            display: none;
        }}
        .modal-triggers-section strong {{
            color: #667eea;
        }}
        .modal-triggers-section code {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .modal-body {{
            padding: 0;
            overflow-y: auto;
            flex: 1;
        }}
        .modal-body iframe {{
            width: 100%;
            border: none;
            min-height: 600px;
            display: block;
        }}
        .modal-footer {{
            padding: 15px 30px;
            background: #f5f5f5;
            border-radius: 0 0 12px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .modal-footer .info {{
            font-size: 12px;
            color: #666;
        }}
        .modal-footer .btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
        }}
        .modal-footer .btn:hover {{
            background: #764ba2;
        }}
        
        @media (max-width: 768px) {{
            .message-list {{
                grid-template-columns: 1fr;
            }}
            .modal-content {{
                margin: 10px;
                max-height: 95vh;
            }}
            .modal-header {{
                padding: 15px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📧 Email Message Gallery</h1>
            <p>All TransitionMessage Notifications Across Bluebottle</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <span class="stat-number">{total_messages}</span>
                <span class="stat-label">Total Messages</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{len(all_messages)}</span>
                <span class="stat-label">Modules</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{len(languages)}</span>
                <span class="stat-label">Languages</span>
            </div>
        </div>
"""
    
    for module_name, messages in sorted(all_messages.items()):
        module_dir = module_name.replace('.', '_')
        html += f"""
        <div class="module-section">
            <h2>{module_name} ({len(messages)} messages)</h2>
            <div class="message-list">
"""
        for msg_name, msg_class in sorted(messages):
            doc = (msg_class.__doc__ or "").strip().replace('\n', ' ')
            
            # Get trigger info from metadata
            triggers = trigger_map.get(msg_name, []) if trigger_map else []
            trigger_desc = format_trigger_description(triggers) if triggers else ""
            
            html += f"""
                <div class="message-item">
                    <div class="message-name">{msg_name}</div>
                    {f'<div class="message-description">{doc}</div>' if doc else ''}
                    {f'<div class="message-triggers"><strong>🎯 Triggered by:</strong> {trigger_desc}</div>' if trigger_desc else ''}
                    <div class="lang-links">
"""
            # Show only EN and NL buttons in the overview
            overview_languages = [lang for lang in ['en', 'nl'] if lang in languages]
            for lang in overview_languages:
                # Language flags
                lang_flags = {
                    'de': '🇩🇪', 'en': '🇬🇧', 'es': '🇪🇸',
                    'fr': '🇫🇷', 'hu': '🇭🇺', 'nl': '🇳🇱', 'pt': '🇵🇹'
                }
                lang_flag = lang_flags.get(lang, '🌐')
                html += f'                        <button class="lang-btn" onclick="openModal(\'{module_name}\', \'{msg_name}\', \'{lang}\')">{lang_flag} {lang.upper()}</button>\n'
            
            html += """                    </div>
                </div>
"""
        html += """            </div>
        </div>
"""
    
    # Add Modal HTML and JavaScript
    html += """    </div>
    
    <!-- Modal -->
    <div id="email-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title">Email Preview</h2>
                <div class="modal-controls">
                    <div id="modal-lang-selector"></div>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
            </div>
            <div id="modal-triggers" class="modal-triggers-section"></div>
            <div id="modal-subject" class="modal-subject"></div>
            <div class="modal-body">
                <iframe id="modal-iframe" src="about:blank"></iframe>
            </div>
            <div class="modal-footer">
                <div class="info">Press ESC to close or click outside</div>
                <a id="modal-open-new" href="#" target="_blank" class="btn">Open in New Tab</a>
            </div>
        </div>
    </div>

    <script>
        let metadata = null;
        let currentModule = null;
        let currentMessage = null;
        let currentLanguage = 'en';
        
        // Load metadata
        async function loadMetadata() {
            try {
                const response = await fetch('metadata_all.json');
                metadata = await response.json();
            } catch (error) {
                console.error('Error loading metadata:', error);
            }
        }
        
        function openModal(moduleName, messageName, language = 'en') {
            if (!metadata) {
                console.error('Metadata not loaded');
                return;
            }
            
            const moduleData = metadata.modules[moduleName];
            if (!moduleData) {
                console.error('Module not found:', moduleName);
                return;
            }
            
            const messageData = moduleData.messages.find(m => m.name === messageName);
            if (!messageData || !messageData.previews[language]) {
                console.error('Message or language not found');
                return;
            }
            
            currentModule = moduleName;
            currentMessage = messageData;
            currentLanguage = language;
            
            const modal = document.getElementById('email-modal');
            const iframe = document.getElementById('modal-iframe');
            const title = document.getElementById('modal-title');
            const subjectDiv = document.getElementById('modal-subject');
            const triggersDiv = document.getElementById('modal-triggers');
            const openNew = document.getElementById('modal-open-new');
            const langSelector = document.getElementById('modal-lang-selector');
            
            // Set title
            title.textContent = messageName;
            
            // Set subject if available
            if (messageData.subjects && messageData.subjects[language]) {
                subjectDiv.textContent = '📧 Subject: ' + messageData.subjects[language];
                subjectDiv.style.display = 'block';
            } else {
                subjectDiv.textContent = '';
                subjectDiv.style.display = 'none';
            }
            
            // Set trigger information if available
            if (messageData.trigger_description) {
                triggersDiv.innerHTML = '<strong>🎯 Triggered by:</strong> ' + messageData.trigger_description;
                triggersDiv.style.display = 'block';
            } else {
                triggersDiv.innerHTML = '';
                triggersDiv.style.display = 'none';
            }
            
            // Load preview in iframe
            iframe.src = messageData.previews[language];
            
            // Update "Open in New Tab" link
            openNew.href = messageData.previews[language];
            
            // Render language selector with proper flags
            const langFlags = {
                'de': '🇩🇪', 'en': '🇬🇧', 'es': '🇪🇸',
                'fr': '🇫🇷', 'hu': '🇭🇺', 'nl': '🇳🇱', 'pt': '🇵🇹'
            };
            
            langSelector.innerHTML = metadata.languages
                .filter(lang => messageData.previews[lang])
                .map(lang => `
                    <button 
                        class="modal-lang-btn ${lang === language ? 'active' : ''}" 
                        onclick="switchLanguage('${lang}')">
                        ${langFlags[lang] || '🌐'} ${lang.toUpperCase()}
                    </button>
                `).join('');
            
            // Show modal
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        
        function switchLanguage(language) {
            if (currentMessage && currentMessage.previews[language]) {
                currentLanguage = language;
                const iframe = document.getElementById('modal-iframe');
                const subjectDiv = document.getElementById('modal-subject');
                const openNew = document.getElementById('modal-open-new');
                const langSelector = document.getElementById('modal-lang-selector');
                
                iframe.src = currentMessage.previews[language];
                openNew.href = currentMessage.previews[language];
                
                // Update subject
                if (currentMessage.subjects && currentMessage.subjects[language]) {
                    subjectDiv.textContent = '📧 Subject: ' + currentMessage.subjects[language];
                    subjectDiv.style.display = 'block';
                } else {
                    subjectDiv.textContent = '';
                    subjectDiv.style.display = 'none';
                }
                
                // Re-render language selector with updated active state
                const langFlags = {
                    'de': '🇩🇪', 'en': '🇬🇧', 'es': '🇪🇸',
                    'fr': '🇫🇷', 'hu': '🇭🇺', 'nl': '🇳🇱', 'pt': '🇵🇹'
                };
                
                langSelector.innerHTML = metadata.languages
                    .filter(lang => currentMessage.previews[lang])
                    .map(lang => `
                        <button 
                            class="modal-lang-btn ${lang === language ? 'active' : ''}" 
                            onclick="switchLanguage('${lang}')">
                            ${langFlags[lang] || '🌐'} ${lang.toUpperCase()}
                        </button>
                    `).join('');
            }
        }
        
        function closeModal() {
            const modal = document.getElementById('email-modal');
            const iframe = document.getElementById('modal-iframe');
            
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
            
            // Clear iframe after animation
            setTimeout(() => {
                iframe.src = 'about:blank';
            }, 300);
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('email-modal');
            if (event.target === modal) {
                closeModal();
            }
        }
        
        // Close modal with ESC key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeModal();
            }
        });
        
        // Load metadata on page load
        loadMetadata();
    </script>
</body>
</html>"""
    
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Generated index: {index_path}")
    return index_path

class Command(BaseCommand):
    help = 'Preview all email messages across Bluebottle with modal support'
    
    def add_arguments(self, parser):
        parser.add_argument('--list-modules', action='store_true', help='List all available modules')
        parser.add_argument('--module', type=str, help='Generate previews for specific module')
        parser.add_argument('--all', action='store_true', help='Generate previews for ALL modules')
        parser.add_argument('--all-languages', action='store_true', 
                           help='Generate in all available languages (de, en, es, fr, hu, nl, pt)')
        parser.add_argument('--languages', type=str,
                           help='Comma-separated language codes (e.g., "en,nl,fr")')
        parser.add_argument('--output-dir', type=str, 
                           default=None,
                           help='Output directory (default: notifications/static/email_previews)')
    
    def handle(self, *args, **options):
        # Set up a real tenant for the preview generation
        try:
            tenant = Client.objects.first()
            if tenant:
                connection.set_tenant(tenant)
                self.stdout.write(f"Using tenant: {tenant.client_name}")
            else:
                self.stderr.write("Warning: No tenant found in database. Some features may not work correctly.")
        except Exception as e:
            self.stderr.write(f"Warning: Could not set up tenant: {e}")
        
        # Set default output directory to static folder
        if not options['output_dir']:
            options['output_dir'] = os.path.join(
                settings.BASE_DIR,
                'mails',
            )
        
        if options['list_modules']:
            self.stdout.write("\n📦 Available Message Modules:")
            self.stdout.write("="*80)
            for short_name, full_path in sorted(MESSAGE_MODULES.items()):
                messages = discover_message_classes(full_path)
                self.stdout.write(f"  {short_name:40} ({len(messages)} messages)")
            self.stdout.write(f"\n Total modules: {len(MESSAGE_MODULES)}")
            return
        
        # Determine which languages to generate
        available_languages = ['de', 'en', 'es', 'fr', 'hu', 'nl', 'pt']
        if options.get('languages'):
            languages = [lang.strip() for lang in options['languages'].split(',')]
            # Validate languages
            invalid = [lang for lang in languages if lang not in available_languages]
            if invalid:
                self.stderr.write(f"Invalid language codes: {', '.join(invalid)}")
                self.stdout.write(f"Available languages: {', '.join(available_languages)}")
                return
        elif options['all_languages']:
            languages = available_languages
        else:
            languages = ['en']
        
        self.stdout.write(f"Generating previews for languages: {', '.join(languages)}\n")
        
        if options['all'] or options['module']:
            modules_to_process = {}
            
            if options['all']:
                modules_to_process = MESSAGE_MODULES
            elif options['module']:
                # Find matching module
                matched = {k: v for k, v in MESSAGE_MODULES.items() if options['module'].lower() in k.lower()}
                if not matched:
                    self.stderr.write(f"❌ No module found matching '{options['module']}'")
                    self.stdout.write("\nAvailable modules:")
                    for name in MESSAGE_MODULES.keys():
                        self.stdout.write(f"  - {name}")
                    return
                modules_to_process = matched
            
            # Analyze triggers to map messages to their triggering transitions
            self.stdout.write("\n🔍 Analyzing trigger files...")
            trigger_map = analyze_triggers()
            self.stdout.write(f"   Found trigger info for {len(trigger_map)} message classes\n")
            
            all_messages = {}
            total_generated = 0
            subjects_cache = {}  # Cache for subjects
            
            for module_name, module_path in modules_to_process.items():
                self.stdout.write(f"\n{'='*80}")
                self.stdout.write(f"📦 Processing module: {module_name}")
                self.stdout.write(f"{'='*80}")
                
                messages = discover_message_classes(module_path)
                if not messages:
                    self.stdout.write(f"  No messages found in {module_name}")
                    continue
                
                all_messages[module_name] = messages
                self.stdout.write(f"  Found {len(messages)} message classes")
                
                for msg_name, msg_class in messages:
                    for lang in languages:
                        content = preview_message(msg_name, msg_class, lang, 'html')
                        if content:
                            result = save_preview(msg_name, content, options['output_dir'], module_name, lang)
                            # Cache the subject
                            if result and result.get('subject'):
                                cache_key = f"{module_name}:{msg_name}:{lang}"
                                subjects_cache[cache_key] = result['subject']
                            total_generated += 1
            
            # Save subjects cache
            if subjects_cache:
                subject_cache_file = os.path.join(options['output_dir'], '.subjects_cache.json')
                with open(subject_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(subjects_cache, f, indent=2)
            
            # Generate comprehensive index
            if all_messages:
                generate_index(options['output_dir'], all_messages, languages, trigger_map)
            
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(self.style.SUCCESS(f"✅ COMPLETE!"))
            self.stdout.write(f"{'='*80}")
            self.stdout.write(f"Total messages generated: {total_generated}")
            self.stdout.write(f"Output directory: {os.path.abspath(options['output_dir'])}")
            self.stdout.write(f"\nView in browser:")
            self.stdout.write(f"  Static URL: /static/email_previews/index_all.html")
            self.stdout.write(f"  Or open: xdg-open {os.path.abspath(options['output_dir'])}/index_all.html")
        
        else:
            self.print_help('manage.py', 'preview_all_messages')

