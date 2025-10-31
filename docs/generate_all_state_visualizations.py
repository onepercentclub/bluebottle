#!/usr/bin/env python3
"""
Master script to generate HTML visualizations for ALL state machines
in the Bluebottle platform.

This will create comprehensive documentation for:
- Time-Based Activities (Date, Deadline, Schedule, Periodic, etc.)
- Funding Activities
- Collect Activities  
- Grant Applications
- Initiatives
- All participant/contributor types
- Teams, Slots, Payments, etc.
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collections import defaultdict

# Activity type configurations
ACTIVITY_TYPES = {
    'time_based': {
        'name': 'Time-Based Activities',
        'description': 'Activities with dates, deadlines, or schedules where volunteers contribute their time',
        'states_file': 'bluebottle/time_based/states/states.py',
        'triggers_file': 'bluebottle/time_based/triggers/activities.py',
        'models': {
            'DateActivity': 'Activities on specific dates',
            'DeadlineActivity': 'Activities with deadlines',
            'ScheduleActivity': 'Activities with flexible schedules',
            'PeriodicActivity': 'Recurring activities',
            'PeriodActivity': 'Activities during a period'
        }
    },
    'funding': {
        'name': 'Funding/Crowdfunding',
        'description': 'Crowdfunding campaigns where people donate money',
        'states_file': 'bluebottle/funding/states.py',
        'triggers_file': 'bluebottle/funding/triggers/funding.py',
        'models': {
            'Funding': 'Crowdfunding campaign',
            'Donor': 'Donor contributor'
        }
    },
    'deeds': {
        'name': 'Deeds',
        'description': 'Simple activities where people sign up to participate',
        'states_file': 'bluebottle/deeds/states.py',
        'triggers_file': 'bluebottle/deeds/triggers.py',
        'models': {
            'Deed': 'Deed activity',
            'DeedParticipant': 'Deed participant'
        },
        'status': 'COMPLETED ✅'
    },
    'collect': {
        'name': 'Collect Activities',
        'description': 'Activities where people collect and contribute items',
        'states_file': 'bluebottle/collect/states.py',
        'triggers_file': 'bluebottle/collect/triggers.py',
        'models': {
            'CollectActivity': 'Collection activity',
            'CollectContributor': 'Collection contributor'
        }
    },
    'grant_management': {
        'name': 'Grant Applications',
        'description': 'Grant application and management system',
        'states_file': 'bluebottle/grant_management/states.py',
        'triggers_file': 'bluebottle/grant_management/triggers.py',
        'models': {
            'GrantApplication': 'Grant application',
            'GrantDonor': 'Grant donor'
        }
    },
    'initiatives': {
        'name': 'Initiatives',
        'description': 'Parent initiatives that contain activities',
        'states_file': 'bluebottle/initiatives/states.py',
        'triggers_file': 'bluebottle/initiatives/triggers.py',
        'models': {
            'Initiative': 'Initiative/Campaign'
        }
    }
}

# Participant types
PARTICIPANT_TYPES = {
    'time_based_participants': {
        'name': 'Time-Based Participants',
        'description': 'Participants in time-based activities',
        'states_file': 'bluebottle/time_based/states/participants.py',
        'triggers_file': 'bluebottle/time_based/triggers/participants.py',
        'models': {
            'DateParticipant': 'Date activity participant',
            'DeadlineParticipant': 'Deadline activity participant',
            'ScheduleParticipant': 'Schedule activity participant',
            'TeamScheduleParticipant': 'Team schedule participant',
            'PeriodicParticipant': 'Periodic activity participant'
        }
    },
    'teams': {
        'name': 'Teams',
        'description': 'Team management for team-based activities',
        'states_file': 'bluebottle/time_based/states/teams.py',
        'triggers_file': 'bluebottle/time_based/triggers/teams.py',
        'models': {
            'Team': 'Team',
            'TeamMember': 'Team member'
        }
    },
    'slots': {
        'name': 'Activity Slots',
        'description': 'Time slots for scheduled activities',
        'states_file': 'bluebottle/time_based/states/slots.py',
        'triggers_file': 'bluebottle/time_based/triggers/slots.py',
        'models': {
            'Slot': 'Activity slot',
            'PeriodicSlot': 'Periodic slot',
            'ScheduleSlot': 'Schedule slot',
            'TeamScheduleSlot': 'Team schedule slot'
        }
    }
}

def print_summary():
    """Print summary of all state machines to document"""
    print("=" * 80)
    print("BLUEBOTTLE STATE MACHINE DOCUMENTATION GENERATOR")
    print("=" * 80)
    print()
    
    print("📊 ACTIVITY TYPES TO DOCUMENT:")
    print("-" * 80)
    for key, config in ACTIVITY_TYPES.items():
        status = config.get('status', '⏳ Pending')
        print(f"\n{config['name']} - {status}")
        print(f"  {config['description']}")
        print(f"  Models: {', '.join(config['models'].keys())}")
        print(f"  States: {config['states_file']}")
        print(f"  Triggers: {config['triggers_file']}")
    
    print("\n")
    print("👥 PARTICIPANT/CONTRIBUTOR TYPES TO DOCUMENT:")
    print("-" * 80)
    for key, config in PARTICIPANT_TYPES.items():
        print(f"\n{config['name']}")
        print(f"  {config['description']}")
        print(f"  Models: {', '.join(config['models'].keys())}")
        print(f"  States: {config['states_file']}")
        print(f"  Triggers: {config['triggers_file']}")
    
    print("\n")
    print("=" * 80)
    print(f"TOTAL: {len(ACTIVITY_TYPES)} activity type groups")
    print(f"TOTAL: {len(PARTICIPANT_TYPES)} participant type groups")
    
    # Count total models
    total_models = sum(len(config['models']) for config in ACTIVITY_TYPES.values())
    total_models += sum(len(config['models']) for config in PARTICIPANT_TYPES.values())
    print(f"TOTAL MODELS: {total_models}")
    print("=" * 80)
    print()

def main():
    """Main execution"""
    print_summary()
    
    print("🎯 RECOMMENDED APPROACH:")
    print("-" * 80)
    print("Due to the large number of state machines, I recommend:")
    print()
    print("1. Start with the most commonly used activity types:")
    print("   - Time-Based Activities (most complex)")
    print("   - Funding Activities")
    print("   - Collect Activities")
    print()
    print("2. Then document supporting types:")
    print("   - Grant Applications")
    print("   - Initiatives")
    print("   - Teams & Slots")
    print()
    print("3. Create a unified index page linking to all visualizations")
    print()
    print("=" * 80)
    print()
    
    response = input("Do you want to generate documentation for ALL types? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        print("\n🚀 Starting full documentation generation...")
        print("This will take some time...")
        print()
        # Here we would call the actual generation functions
        print("⚠️  This script requires the full generation logic to be implemented.")
        print("Please run specific generators for each activity type.")
    else:
        print("\n💡 Run specific generators instead:")
        print("   python3 generate_deed_state_pages.py (✅ Already done)")
        print("   python3 generate_time_based_state_pages.py (TODO)")
        print("   python3 generate_funding_state_pages.py (TODO)")
        print("   python3 generate_collect_state_pages.py (TODO)")
        print("   etc.")

if __name__ == '__main__':
    main()

