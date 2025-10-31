#!/usr/bin/env python
"""
Generate HTML pages for all Deed and DeedParticipant states
with transitions, effects, conditions, and notifications.
"""

import os

# Define all states and their properties
DEED_STATES = {
    'draft': {
        'name': 'Draft',
        'value': 'draft',
        'description': 'The activity has been created, but not yet completed. An activity manager is still editing the activity.',
        'header_class': 'draft-header',
        'outgoing': [
            {
                'name': 'submit',
                'to': 'submitted',
                'type': 'manual',
                'description': 'The activity will be submitted for review.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'can_submit() - The activity can be submitted'
                ]
            },
            {
                'name': 'auto_submit',
                'to': 'submitted',
                'type': 'automatic',
                'description': 'The activity will be submitted for review automatically.',
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct'
                ]
            },
            {
                'name': 'publish',
                'to': 'open',
                'type': 'manual',
                'description': 'Your activity will be open to contributions.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'can_publish() - The activity can be published'
                ]
            },
            {
                'name': 'auto_publish',
                'to': 'open',
                'type': 'automatic',
                'description': 'Automatically publish activity when initiative is approved.',
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'should_auto_approve() - The activity should be approved automatically'
                ]
            },
            {
                'name': 'approve',
                'to': 'open',
                'type': 'manual',
                'description': 'The activity will be published and visible in the frontend for people to contribute to.',
                'permission': ['is_staff - User is a staff member or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'should_auto_approve() - The activity should be approved automatically'
                ]
            },
            {
                'name': 'reject',
                'to': 'rejected',
                'type': 'manual',
                'description': 'Reject if the activity does not align with your program or guidelines.',
                'permission': ['is_staff - User is a staff member or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': "Fail organizer (OrganizerStateMachine.fail)"
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRejectedNotification',
                        'subject': 'Your activity "{title}" has been rejected',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'delete',
                'to': 'deleted',
                'type': 'manual',
                'description': 'Delete the activity if you do not want it to be included in the report.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser']
            }
        ],
        'incoming': [
            {
                'name': 'initiate',
                'from': 'EmptyState',
                'type': 'automatic',
                'description': 'The activity will be created.'
            },
            {
                'name': 'reopen_manually',
                'from': ['succeeded', 'expired'],
                'type': 'manual',
                'description': 'The activity will be set to the status \'Needs work\'. Then you can make changes to the activity and submit it again.'
            }
        ]
    },
    'submitted': {
        'name': 'Submitted',
        'value': 'submitted',
        'description': 'The activity has been submitted and is ready to be reviewed.',
        'header_class': 'submitted-header',
        'outgoing': [
            {
                'name': 'approve',
                'to': 'open',
                'type': 'manual',
                'description': 'The activity will be published and visible in the frontend for people to contribute to.',
                'permission': ['is_staff - User is a staff member or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'should_auto_approve() - The activity should be approved automatically'
                ]
            },
            {
                'name': 'auto_approve',
                'to': 'open',
                'type': 'automatic',
                'description': 'The activity will be visible in the frontend and people can apply to the activity.',
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'should_auto_approve() - The activity should be approved automatically'
                ],
                'effects': [
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Reopen if not finished',
                        'condition': 'is_not_finished'
                    },
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Succeed if finished and has participants',
                        'condition': 'is_finished AND has_participants'
                    },
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Expire if finished and has no participants',
                        'condition': 'is_finished AND has_no_participants'
                    }
                ]
            },
            {
                'name': 'publish',
                'to': 'open',
                'type': 'manual',
                'description': 'Your activity will be open to contributions.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'can_publish() - The activity can be published'
                ],
                'effects': [
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Reopen if not finished',
                        'condition': 'is_not_finished'
                    },
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Succeed if finished and has participants',
                        'condition': 'is_finished AND has_participants'
                    },
                    {
                        'type': 'ConditionalTransitionEffect',
                        'description': 'Expire if finished and has no participants',
                        'condition': 'is_finished AND has_no_participants'
                    },
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed organizer if has organizer',
                        'condition': 'has_organizer'
                    }
                ]
            },
            {
                'name': 'request_changes',
                'to': 'needs_work',
                'type': 'manual',
                'description': 'The activity needs changes before it can be approved.',
                'permission': ['is_staff - User is a staff member or superuser']
            },
            {
                'name': 'reject',
                'to': 'rejected',
                'type': 'manual',
                'description': 'Reject if the activity does not align with your program or guidelines.',
                'permission': ['is_staff - User is a staff member or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': "Fail organizer"
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRejectedNotification',
                        'subject': 'Your activity "{title}" has been rejected',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'expire',
                'to': 'expired',
                'type': 'automatic',
                'description': 'The activity will be cancelled because no one has signed up for the registration deadline.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': "Fail organizer"
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityExpiredNotification',
                        'subject': 'The registration deadline for your activity "{title}" has expired',
                        'recipient': 'Activity owner'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'submit',
                'from': ['draft', 'needs_work'],
                'type': 'manual',
                'description': 'The activity will be submitted for review.'
            },
            {
                'name': 'auto_submit',
                'from': ['draft', 'needs_work'],
                'type': 'automatic',
                'description': 'The activity will be submitted for review automatically.'
            }
        ]
    },
    'needs_work': {
        'name': 'Needs Work',
        'value': 'needs_work',
        'description': 'The activity needs changes before it can be approved.',
        'header_class': 'needs-work-header',
        'outgoing': [
            {
                'name': 'submit',
                'to': 'submitted',
                'type': 'manual',
                'description': 'The activity will be submitted for review.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'can_submit() - The activity can be submitted'
                ]
            },
            {
                'name': 'auto_submit',
                'to': 'submitted',
                'type': 'automatic',
                'description': 'The activity will be submitted for review automatically.',
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct'
                ]
            },
            {
                'name': 'publish',
                'to': 'open',
                'type': 'manual',
                'description': 'Your activity will be open to contributions.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'can_publish() - The activity can be published'
                ]
            },
            {
                'name': 'approve',
                'to': 'open',
                'type': 'manual',
                'description': 'The activity will be published and visible in the frontend for people to contribute to.',
                'permission': ['is_staff - User is a staff member or superuser'],
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'should_auto_approve() - The activity should be approved automatically'
                ]
            },
            {
                'name': 'reject',
                'to': 'rejected',
                'type': 'manual',
                'description': 'Reject if the activity does not align with your program or guidelines.',
                'permission': ['is_staff - User is a staff member or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': "Fail organizer"
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRejectedNotification',
                        'subject': 'Your activity "{title}" has been rejected',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'delete',
                'to': 'deleted',
                'type': 'manual',
                'description': 'Delete the activity if you do not want it to be included in the report.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser']
            }
        ],
        'incoming': [
            {
                'name': 'request_changes',
                'from': ['submitted'],
                'type': 'manual',
                'description': 'The activity needs changes before it can be approved.'
            },
            {
                'name': 'restore',
                'from': ['rejected', 'cancelled', 'deleted', 'expired'],
                'type': 'manual',
                'description': 'The activity status is changed to \'Needs work\'.'
            }
        ]
    },
    'open': {
        'name': 'Open',
        'value': 'open',
        'description': 'The activity is accepting new contributions.',
        'header_class': 'open-header',
        'outgoing': [
            {
                'name': 'succeed',
                'to': 'succeeded',
                'type': 'automatic',
                'description': 'The activity ends successfully.',
                'conditions': ['can_succeed() - Has at least one participant'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed all participants (if not started)',
                        'condition': 'is_not_started'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivitySucceededNotification',
                        'subject': 'Your activity "{title}" has succeeded 🎉',
                        'recipient': 'Activity owner'
                    },
                    {
                        'type': 'SetEndDateEffect',
                        'description': 'Set end date to today if not set'
                    }
                ]
            },
            {
                'name': 'succeed_manually',
                'to': 'succeeded',
                'type': 'manual',
                'description': 'The activity ends and people can no longer register.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'conditions': [
                    'has_no_end_date() - Deed has no end date set',
                    'can_succeed() - Has at least one participant'
                ],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed all participants (if not started)',
                        'condition': 'is_not_started'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivitySucceededNotification',
                        'subject': 'Your activity "{title}" has succeeded 🎉',
                        'recipient': 'Activity owner'
                    },
                    {
                        'type': 'SetEndDateEffect',
                        'description': 'Set end date to today if not set'
                    }
                ]
            },
            {
                'name': 'expire',
                'to': 'expired',
                'type': 'automatic',
                'description': 'The activity will be cancelled because no one has signed up for the registration deadline.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityExpiredNotification',
                        'subject': 'The registration deadline for your activity "{title}" has expired',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'cancel',
                'to': 'cancelled',
                'type': 'manual',
                'description': 'Cancel if the activity will not be executed.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityCancelledNotification',
                        'subject': 'Your activity "{title}" has been cancelled',
                        'recipient': 'Activity owner'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'publish',
                'from': ['submitted', 'draft', 'needs_work'],
                'type': 'manual',
                'description': 'Your activity will be open to contributions.'
            },
            {
                'name': 'auto_publish',
                'from': ['submitted', 'draft', 'needs_work'],
                'type': 'automatic',
                'description': 'Automatically publish activity when initiative is approved.'
            },
            {
                'name': 'approve',
                'from': ['submitted', 'needs_work', 'draft'],
                'type': 'manual',
                'description': 'The activity will be published and visible in the frontend.'
            },
            {
                'name': 'auto_approve',
                'from': ['submitted', 'rejected'],
                'type': 'automatic',
                'description': 'The activity will be visible in the frontend and people can apply.'
            },
            {
                'name': 'reopen',
                'from': ['rejected', 'cancelled', 'deleted', 'expired'],
                'type': 'automatic',
                'description': 'Open the activity again.'
            }
        ],
        'triggers': [
            {
                'type': 'ModelChangedTrigger',
                'field': 'end',
                'description': 'When end date changes',
                'effects': [
                    'Reopen if not finished',
                    'Succeed if finished and has participants',
                    'Expire if finished and has no participants',
                    'Reschedule all effort contributions',
                    'Send DeedDateChangedNotification to participants (if not finished)'
                ]
            },
            {
                'type': 'ModelChangedTrigger',
                'field': 'start',
                'description': 'When start date changes',
                'effects': [
                    'Re-accept participants if has start date and not started',
                    'Succeed participants if started',
                    'Reschedule all effort contributions',
                    'Send DeedDateChangedNotification to participants (if not started)'
                ]
            }
        ]
    },
    'succeeded': {
        'name': 'Succeeded',
        'value': 'succeeded',
        'description': 'The activity has ended successfully.',
        'header_class': 'succeeded-header',
        'outgoing': [
            {
                'name': 'reopen',
                'to': 'open',
                'type': 'automatic',
                'description': 'Reopen the activity.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Re-accept participants (if not finished)',
                        'condition': 'is_not_finished'
                    }
                ]
            },
            {
                'name': 'reopen_manually',
                'to': 'draft',
                'type': 'manual',
                'description': 'The activity will be set to the status \'Needs work\'.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser']
            },
            {
                'name': 'cancel',
                'to': 'cancelled',
                'type': 'manual',
                'description': 'Cancel if the activity will not be executed.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityCancelledNotification',
                        'subject': 'Your activity "{title}" has been cancelled',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'expire',
                'to': 'expired',
                'type': 'automatic',
                'description': 'The activity will be cancelled because no one has signed up.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Fail organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityExpiredNotification',
                        'subject': 'The registration deadline for your activity "{title}" has expired',
                        'recipient': 'Activity owner'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'succeed',
                'from': ['open', 'expired'],
                'type': 'automatic',
                'description': 'The activity ends successfully.'
            },
            {
                'name': 'succeed_manually',
                'from': ['open'],
                'type': 'manual',
                'description': 'The activity ends and people can no longer register.'
            }
        ]
    },
    'expired': {
        'name': 'Expired',
        'value': 'expired',
        'description': 'The activity has ended, but did not have any contributions. The activity does not appear on the platform, but counts in the report.',
        'header_class': 'expired-header',
        'outgoing': [
            {
                'name': 'succeed',
                'to': 'succeeded',
                'type': 'automatic',
                'description': 'The activity ends successfully.',
                'conditions': ['can_succeed() - Has at least one participant'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Succeed all participants'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivitySucceededNotification',
                        'subject': 'Your activity "{title}" has succeeded 🎉',
                        'recipient': 'Activity owner'
                    },
                    {
                        'type': 'SetEndDateEffect',
                        'description': 'Set end date to today if not set'
                    }
                ]
            },
            {
                'name': 'reopen',
                'to': 'open',
                'type': 'automatic',
                'description': 'Reopen the activity.',
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Re-accept participants (if not finished)'
                    }
                ]
            },
            {
                'name': 'reopen_manually',
                'to': 'draft',
                'type': 'manual',
                'description': 'The activity will be set to the status \'Needs work\'.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser']
            },
            {
                'name': 'restore',
                'to': 'needs_work',
                'type': 'manual',
                'description': 'The activity status is changed to \'Needs work\'.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Reset organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRestoredNotification',
                        'subject': 'The activity "{title}" has been restored',
                        'recipient': 'Activity owner'
                    }
                ]
            }
        ],
        'incoming': [
            {
                'name': 'expire',
                'from': ['open', 'submitted', 'succeeded'],
                'type': 'automatic',
                'description': 'The activity will be cancelled because no one has signed up.'
            }
        ]
    },
    'cancelled': {
        'name': 'Cancelled',
        'value': 'cancelled',
        'description': 'The activity is not executed. The activity does not appear on the platform, but counts in the report.',
        'header_class': 'cancelled-header',
        'outgoing': [
            {
                'name': 'restore',
                'to': 'needs_work',
                'type': 'manual',
                'description': 'The activity status is changed to \'Needs work\'.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Reset organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRestoredNotification',
                        'subject': 'The activity "{title}" has been restored',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'reopen',
                'to': 'open',
                'type': 'automatic',
                'description': 'Open the activity again.'
            }
        ],
        'incoming': [
            {
                'name': 'cancel',
                'from': ['open', 'succeeded'],
                'type': 'manual',
                'description': 'Cancel if the activity will not be executed.'
            }
        ]
    },
    'rejected': {
        'name': 'Rejected',
        'value': 'rejected',
        'description': 'The activity does not fit the programme or does not comply with the rules. The activity does not appear on the platform, but counts in the report.',
        'header_class': 'rejected-header',
        'outgoing': [
            {
                'name': 'auto_approve',
                'to': 'open',
                'type': 'automatic',
                'description': 'The activity will be visible in the frontend and people can apply.',
                'conditions': [
                    'is_complete() - All required information has been submitted',
                    'is_valid() - All fields passed validation and are correct',
                    'should_auto_approve() - The activity should be approved automatically'
                ]
            },
            {
                'name': 'restore',
                'to': 'needs_work',
                'type': 'manual',
                'description': 'The activity status is changed to \'Needs work\'.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Reset organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRestoredNotification',
                        'subject': 'The activity "{title}" has been restored',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'reopen',
                'to': 'open',
                'type': 'automatic',
                'description': 'Open the activity again.'
            }
        ],
        'incoming': [
            {
                'name': 'reject',
                'from': ['draft', 'needs_work', 'submitted'],
                'type': 'manual',
                'description': 'Reject if the activity does not align with your program or guidelines.'
            }
        ]
    },
    'deleted': {
        'name': 'Deleted',
        'value': 'deleted',
        'description': 'The activity has been removed. The activity does not appear on the platform and does not count in the report.',
        'header_class': 'deleted-header',
        'outgoing': [
            {
                'name': 'restore',
                'to': 'needs_work',
                'type': 'manual',
                'description': 'The activity status is changed to \'Needs work\'.',
                'permission': ['is_owner - User is the activity owner, staff, or superuser'],
                'effects': [
                    {
                        'type': 'RelatedTransitionEffect',
                        'description': 'Reset organizer'
                    },
                    {
                        'type': 'NotificationEffect',
                        'notification': 'ActivityRestoredNotification',
                        'subject': 'The activity "{title}" has been restored',
                        'recipient': 'Activity owner'
                    }
                ]
            },
            {
                'name': 'reopen',
                'to': 'open',
                'type': 'automatic',
                'description': 'Open the activity again.'
            }
        ],
        'incoming': [
            {
                'name': 'delete',
                'from': ['draft', 'needs_work'],
                'type': 'manual',
                'description': 'Delete the activity if you do not want it to be included in the report.'
            }
        ]
    }
}

# Participant states would be defined similarly...
# For brevity, I'll create a template generation function

def generate_state_html(state_key, state_data, is_participant=False):
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
                        </li>
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
                    <div class="trigger-type">{trigger["type"]}: {trigger.get("field", "")}</div>
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

# Generate all deed state pages
output_dir = "deed_states_visualization"
os.makedirs(output_dir, exist_ok=True)

for state_key, state_data in DEED_STATES.items():
    filename, html = generate_state_html(state_key, state_data, is_participant=False)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated: {filepath}")

print(f"\n✅ Generated {len(DEED_STATES)} Deed state pages in {output_dir}/")
print("Open deed_states_visualization/index.html in your browser to view the visualization.")

