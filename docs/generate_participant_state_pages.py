#!/usr/bin/env python3
"""
Generate HTML pages for DeedParticipant states
with transitions, effects, conditions, and notifications.
"""

import os

# Define participant states
PARTICIPANT_STATES = {
    'accepted': {
        'name': 'Accepted',
        'value': 'accepted',
        'description': 'This person has been signed up for the activity and was accepted automatically.',
        'header_class': 'accepted-header',
        'outgoing': [
            {
                'name': 'succeed',
                'to': 'succeeded',
                'type': 'automatic',
                'description': 'The contribution was successful.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed activity if it is finished',
                        'condition': 'activity_is_finished'
                    },
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed effort contributions',
                        'condition': 'contributor_is_active'
                    }
                ]
            },
            {
                'name': 'withdraw',
                'to': 'withdrawn',
                'type': 'manual',
                'description': 'Stop your participation in the activity.',
                'permission': ['is_user - The participant themselves'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail effort contributions'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantWithdrewNotification',
                        'subject': 'A participant has withdrawn from your activity "{title}"',
                        'recipient': 'Activity owner'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantWithdrewConfirmationNotification',
                        'subject': 'You have withdrawn from the activity "{title}"',
                        'recipient': 'Participant'
                    },
                    {
                        'type': 'UnFollowActivityEffect',
                        'description': 'User unfollows the activity'
                    }
                ]
            },
            {
                'name': 'remove',
                'to': 'rejected',
                'type': 'manual',
                'description': 'Remove participant from the activity.',
                'permission': ['is_owner - Activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Expire activity if finished and will be empty',
                        'condition': 'activity_is_finished AND activity_will_be_empty'
                    },
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail effort contributions'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantRemovedOwnerNotification',
                        'subject': 'A participant has been removed from your activity "{title}"',
                        'recipient': 'Activity owner',
                        'condition': 'is_not_owner'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantRemovedNotification',
                        'subject': 'You have been removed as participant for the activity "{title}"',
                        'recipient': 'Participant',
                        'condition': 'is_not_owner'
                    },
                    {
                        'type': 'UnFollowActivityEffect',
                        'description': 'User unfollows the activity'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'initiate',
                'from': 'EmptyState',
                'type': 'automatic',
                'description': 'The contribution was created.'
            },
            {
                'name': 're_accept',
                'from': ['succeeded'],
                'type': 'automatic',
                'description': 'Put a participant back as participating after it was successful.'
            },
            {
                'name': 'reapply',
                'from': ['withdrawn'],
                'type': 'manual',
                'description': 'Reapply after previously withdrawing.'
            },
            {
                'name': 'accept',
                'from': ['rejected', 'withdrawn'],
                'type': 'manual',
                'description': 'Reaccept user after previously withdrawing or rejecting.'
            }
        ],
        'triggers': [
            {
                'type': 'TransitionTrigger',
                'trigger': 'initiate',
                'description': 'When participant is created',
                'effects': [
                    'Succeed immediately if activity already started',
                    'Create EffortContribution',
                    'Send NewParticipantNotification to owner (if user joins)',
                    'Send ParticipantAddedNotification to user (if added by manager, active)',
                    'Send InactiveParticipantAddedNotification to user (if added by manager, inactive)',
                    'Send ManagerParticipantAddedOwnerNotification to owner (if added by manager)',
                    'Send ParticipantJoinedNotification to user (if user joins)',
                    'Follow activity'
                ]
            }
        ]
    },
    'succeeded': {
        'name': 'Succeeded',
        'value': 'succeeded',
        'description': 'The contribution was successful.',
        'header_class': 'succeeded-header',
        'outgoing': [
            {
                'name': 're_accept',
                'to': 'accepted',
                'type': 'automatic',
                'description': 'Put a participant back as participating after it was successful.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Reset effort contributions'
                    },
                    {
                        'type': 'FollowActivityEffect',
                        'description': 'User follows the activity'
                    }
                ]
            },
            {
                'name': 'withdraw',
                'to': 'withdrawn',
                'type': 'manual',
                'description': 'Stop your participation in the activity.',
                'permission': ['is_user - The participant themselves'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail effort contributions'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantWithdrewNotification',
                        'subject': 'A participant has withdrawn from your activity "{title}"',
                        'recipient': 'Activity owner'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantWithdrewConfirmationNotification',
                        'subject': 'You have withdrawn from the activity "{title}"',
                        'recipient': 'Participant'
                    },
                    {
                        'type': 'UnFollowActivityEffect',
                        'description': 'User unfollows the activity'
                    }
                ]
            },
            {
                'name': 'remove',
                'to': 'rejected',
                'type': 'manual',
                'description': 'Remove participant from the activity.',
                'permission': ['is_owner - Activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Expire activity if finished and will be empty',
                        'condition': 'activity_is_finished AND activity_will_be_empty'
                    },
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail effort contributions'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantRemovedOwnerNotification',
                        'subject': 'A participant has been removed from your activity "{title}"',
                        'recipient': 'Activity owner',
                        'condition': 'is_not_owner'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ParticipantRemovedNotification',
                        'subject': 'You have been removed as participant for the activity "{title}"',
                        'recipient': 'Participant',
                        'condition': 'is_not_owner'
                    },
                    {
                        'type': 'UnFollowActivityEffect',
                        'description': 'User unfollows the activity'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'succeed',
                'from': ['accepted'],
                'type': 'automatic',
                'description': 'The contribution was successful.'
            }
        ],
        'triggers': [
            {
                'type': 'TransitionTrigger',
                'trigger': 'succeed',
                'description': 'When participant succeeds',
                'effects': [
                    'Succeed activity if it is finished',
                    'Succeed effort contributions (if contributor is active)',
                ]
            }
        ]
    },
    'withdrawn': {
        'name': 'Withdrawn',
        'value': 'withdrawn',
        'description': 'This person has withdrawn from the activity.',
        'header_class': 'withdrawn-header',
        'outgoing': [
            {
                'name': 'reapply',
                'to': 'accepted',
                'type': 'manual',
                'description': 'Reapply after previously withdrawing.',
                'permission': ['is_user - The participant themselves'],
                'conditions': ['activity_is_open - Activity status is "open"'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Reset effort contributions'
                    },
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Succeed immediately if activity already started',
                        'condition': 'activity_did_start'
                    },
                    {
                        'type': 'FollowActivityEffect',
                        'description': 'User follows the activity'
                    }
                ]
            },
            {
                'name': 'accept',
                'to': 'accepted',
                'type': 'manual',
                'description': 'Reaccept user after previously withdrawing or rejecting.',
                'permission': ['is_owner - Activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Succeed immediately if activity already started',
                        'condition': 'activity_did_start'
                    },
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed activity if finished and was expired',
                        'condition': 'activity_is_finished AND activity_expired'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'withdraw',
                'from': ['succeeded', 'accepted'],
                'type': 'manual',
                'description': 'Stop your participation in the activity.'
            }
        ],
        'triggers': [
            {
                'type': 'TransitionTrigger',
                'trigger': 'withdraw',
                'description': 'When participant withdraws',
                'effects': [
                    'Fail effort contributions',
                    'Send ParticipantWithdrewNotification to owner',
                    'Send ParticipantWithdrewConfirmationNotification to participant',
                    'Unfollow activity'
                ]
            }
        ]
    },
    'rejected': {
        'name': 'Rejected',
        'value': 'rejected',
        'description': 'This person has been removed from the activity.',
        'header_class': 'rejected-header',
        'outgoing': [
            {
                'name': 'accept',
                'to': 'accepted',
                'type': 'manual',
                'description': 'Reaccept user after previously withdrawing or rejecting.',
                'permission': ['is_owner - Activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Succeed immediately if activity already started',
                        'condition': 'activity_did_start'
                    },
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed activity if finished and was expired',
                        'condition': 'activity_is_finished AND activity_expired'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'remove',
                'from': ['accepted', 'succeeded'],
                'type': 'manual',
                'description': 'Remove participant from the activity.'
            }
        ],
        'triggers': [
            {
                'type': 'TransitionTrigger',
                'trigger': 'remove',
                'description': 'When participant is removed',
                'effects': [
                    'Expire activity if finished and will be empty',
                    'Fail effort contributions',
                    'Send ParticipantRemovedOwnerNotification to owner (if removed by non-owner)',
                    'Send ParticipantRemovedNotification to participant (if removed by non-owner)',
                    'Unfollow activity'
                ]
            }
        ]
    },
    'new': {
        'name': 'New',
        'value': 'new',
        'description': 'The user started a contribution (inherited state, rarely used for DeedParticipant).',
        'header_class': 'new-header',
        'outgoing': [],
        'incoming': []
    },
    'failed': {
        'name': 'Failed',
        'value': 'failed',
        'description': 'The contribution failed (inherited state).',
        'header_class': 'failed-header',
        'outgoing': [],
        'incoming': []
    }
}

def generate_state_html(state_key, state_data, is_participant=True):
    """Generate HTML for a single state page"""
    
    state_type = "participant" if is_participant else "deed"
    filename = f"{state_type}_{state_key}.html"
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{"DeedParticipant" if is_participant else "Deed"} State: {state_data["name"]}</title>
    <link rel="stylesheet" href="state_styles.css">
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Overview</a>
        
        <header class="state-header {state_data['header_class']}">
            <h1>{state_data["name"]}</h1>
            <div class="state-value">{state_data["value"]}</div>
            <p class="state-description">
                {state_data["description"]}
            </p>
        </header>
'''
    
    # Outgoing transitions
    if state_data.get('outgoing'):
        html += '''        <div class="section">
            <h2>📤 Outgoing Transitions</h2>
'''
        
        for trans in state_data['outgoing']:
            trans_type = trans['type']
            html += f'''            
            <div class="transition-card {trans_type}">
                <div class="transition-header">
                    <span class="transition-name">{trans["name"]}</span>
                    <span class="transition-type">{trans_type.title()}</span>
                </div>
                <div class="transition-to">
                    → <a href="{state_type}_{trans["to"]}.html" class="state-link">{trans["to"]}</a>
                </div>
                <div class="transition-description">
                    {trans["description"]}
                </div>
'''
            
            if trans.get('permission'):
                html += '''                
                <div class="details-section">
                    <h4>🔐 Permission Required</h4>
                    <ul>
'''
                for perm in trans['permission']:
                    html += f'                        <li><code>{perm}</code></li>\n'
                html += '''                    </ul>
                </div>
'''
            
            if trans.get('conditions'):
                html += '''                
                <div class="details-section">
                    <h4>✅ Conditions</h4>
                    <ul>
'''
                for cond in trans['conditions']:
                    html += f'                        <li><code>{cond}</code></li>\n'
                html += '''                    </ul>
                </div>
'''
            
            if trans.get('effects'):
                html += '''                
                <div class="details-section">
                    <h4>⚡ Effects</h4>
                    <ul class="effects-list">
'''
                for effect in trans['effects']:
                    if effect.get('notification'):
                        html += f'''                        <li class="notification-item">
                            <div class="effect-type">📧 {effect["type"]}</div>
                            <div class="notification-subject">Subject: {effect["subject"]}</div>
                            <div class="notification-recipient">Recipient: {effect["recipient"]}</div>
'''
                        if effect.get('condition'):
                            html += f'''                            <div class="notification-condition">Condition: {effect["condition"]}</div>
'''
                        html += '''                        </li>
'''
                    else:
                        html += f'''                        <li class="effect-item">
                            <div class="effect-type">{effect["type"]}</div>
                            <div>{effect["description"]}</div>
'''
                        if effect.get('condition'):
                            html += f'''                            <div class="notification-condition">Condition: {effect["condition"]}</div>
'''
                        html += '''                        </li>
'''
                html += '''                    </ul>
                </div>
'''
            
            html += '''            </div>
'''
        
        html += '''        </div>
'''
    else:
        html += '''        <div class="section">
            <h2>📤 Outgoing Transitions</h2>
            <div class="no-content">No outgoing transitions defined for this state.</div>
        </div>
'''
    
    # Incoming transitions
    if state_data.get('incoming'):
        html += '''        
        <div class="section">
            <h2>📥 Incoming Transitions</h2>
'''
        
        for trans in state_data['incoming']:
            from_states = trans['from'] if isinstance(trans['from'], list) else [trans['from']]
            from_links = []
            for from_state in from_states:
                if from_state == 'EmptyState':
                    from_links.append('<em>EmptyState</em>')
                else:
                    from_links.append(f'<a href="{state_type}_{from_state}.html">{from_state}</a>')
            
            html += f'''            
            <div class="incoming-item">
                <strong>{trans["name"]}</strong> from {", ".join(from_links)} ({trans["type"].title()})
                <p>{trans["description"]}</p>
            </div>
'''
        
        html += '''        </div>
'''
    else:
        html += '''        
        <div class="section">
            <h2>📥 Incoming Transitions</h2>
            <div class="no-content">No incoming transitions defined for this state.</div>
        </div>
'''
    
    # Triggers
    if state_data.get('triggers'):
        html += '''        
        <div class="section">
            <h2>🎯 Triggers</h2>
            <div class="triggers-section">
'''
        
        for trigger in state_data['triggers']:
            html += f'''                
                <div class="trigger-item">
                    <div class="trigger-type">{trigger["type"]}: {trigger.get("trigger", "")}</div>
                    <div>{trigger["description"]}</div>
'''
            if trigger.get('effects'):
                html += '''                    <ul>
'''
                for effect in trigger['effects']:
                    html += f'                        <li>{effect}</li>\n'
                html += '''                    </ul>
'''
            html += '''                </div>
'''
        
        html += '''            </div>
        </div>
'''
    
    html += '''    </div>
</body>
</html>
'''
    
    return filename, html

# Generate all participant state pages
output_dir = "deed_states_visualization"
os.makedirs(output_dir, exist_ok=True)

for state_key, state_data in PARTICIPANT_STATES.items():
    filename, html = generate_state_html(state_key, state_data, is_participant=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated: {filepath}")

print(f"\n✅ Generated {len(PARTICIPANT_STATES)} DeedParticipant state pages in {output_dir}/")
print("Open deed_states_visualization/index.html in your browser to view the visualization.")

