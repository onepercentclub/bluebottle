# Email Trigger Analysis Feature

## Summary

The email preview system now automatically analyzes trigger files to show **which transitions trigger each email message**. This makes it easy to understand when and why emails are sent.

## What Was Added

### 1. Trigger Analysis System

The command now scans all trigger files (`triggers.py` and `triggers/*.py`) to build a mapping of:
- **Which state machine transitions** trigger each notification
- **What conditions** must be met for the notification to send
- **Which module** contains the trigger

### 2. Visual Display

#### In the Gallery View
Each message card now shows a **"🎯 Triggered by:"** section with:
- State machine names (e.g., `ActivityStateMachine`, `DeedStateMachine`)
- Transition names (e.g., `approve`, `reject`, `cancel`)
- Condition functions (if any)

Example:
```
🎯 Triggered by: ActivityStateMachine: approve
🎯 Triggered by: DeedStateMachine: cancel, TimeBasedStateMachine: cancel
🎯 Triggered by: FundingStateMachine: reject (when: is_not_funding)
```

#### In the Modal View
When you open an email preview in the modal, the trigger information is displayed prominently in a yellow-highlighted section below the subject line.

## How It Works

### 1. Analysis Process

The `analyze_triggers()` function:
1. Imports all trigger modules
2. Parses the Python source code using regex patterns
3. Finds `NotificationEffect` calls within `TransitionTrigger` blocks
4. Extracts:
   - Transition reference (e.g., `ActivityStateMachine.approve`)
   - Message class name (e.g., `ActivityApprovedNotification`)
   - Condition functions (e.g., `is_not_funding`, `should_review`)

### 2. Trigger Modules Analyzed

```python
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
```

### 3. Example Trigger Detection

Given this code in `activities/triggers.py`:
```python
TransitionTrigger(
    ActivityStateMachine.approve,
    effects=[
        NotificationEffect(
            ActivityApprovedNotification,
            conditions=[is_not_funding]
        ),
    ]
)
```

The system extracts:
- **Transition**: `approve`
- **State Machine**: `ActivityStateMachine`
- **Message**: `ActivityApprovedNotification`
- **Conditions**: `is_not_funding`

### 4. Data Flow

```
Trigger Files → analyze_triggers() → trigger_map (dict)
                                            ↓
                                    generate_index()
                                            ↓
                              metadata_all.json + HTML gallery
```

## Usage

The feature is automatic - just run the preview command as usual:

```bash
# Generate all previews with trigger information
python manage.py preview_all_messages --all --all-languages

# Generate for specific module
python manage.py preview_all_messages --module activities --languages en,nl

# List modules
python manage.py preview_all_messages --list-modules
```

You'll see:
```
🔍 Analyzing trigger files...
   Found trigger info for 74 message classes
```

## Benefits

1. **Documentation**: Instantly see when each email is triggered without reading trigger files
2. **Debugging**: Quickly identify which transitions should send an email
3. **Onboarding**: New developers can understand the email flow visually
4. **Validation**: Verify that all state transitions have appropriate notifications

## Data Structure

### In metadata_all.json

```json
{
  "name": "ActivityApprovedNotification",
  "description": "The activity was approved",
  "triggers": [
    {
      "transition": "approve",
      "state_machine": "ActivityStateMachine",
      "module": "triggers",
      "full_module": "bluebottle.activities.triggers",
      "conditions": ["is_not_funding"]
    }
  ],
  "trigger_description": "<strong>ActivityStateMachine</strong>: <code>approve</code> <small>(when: <code>is_not_funding</code>)</small>",
  "previews": {...},
  "subjects": {...}
}
```

## Limitations

### Known Edge Cases

1. **Dynamic Triggers**: If triggers are registered dynamically at runtime, they won't be detected by the static analysis

2. **Complex Conditions**: Only simple condition function names are extracted, not their logic

3. **Regex Limitations**: Very unusual formatting might not be parsed correctly

### What's Not Captured

- Triggers registered outside the `TRIGGER_MODULES` list
- Signals or other notification mechanisms
- Manual `Message.objects.create()` calls

## Example Output

### ActivityApprovedNotification
- **Triggers**:
  - `ActivityStateMachine.approve` (when: `is_not_funding`)
  
### FundingRejectedMessage
- **Triggers**:
  - `FundingStateMachine.reject`

### ParticipantAddedNotification
- **Triggers**:
  - `DeadlineParticipantStateMachine.add` (when: `participant_is_active`)
  - `ScheduleParticipantStateMachine.add` (when: `is_not_self`, `participant_is_active`)
  - `CollectContributorStateMachine.initiate` (when: `is_not_user`, `participant_is_active`)

## Technical Details

### Functions Added

1. **`analyze_triggers()`** - Main analysis function
   - Returns: `dict[str, list[dict]]` - Message name → trigger info list

2. **`format_trigger_description(triggers)`** - HTML formatter
   - Groups by state machine
   - Shows conditions inline
   - Returns: HTML string

### Files Modified

- `preview_all_messages.py`:
  - Added `analyze_triggers()` function
  - Added `format_trigger_description()` function
  - Updated `generate_index()` to accept and use `trigger_map`
  - Updated `handle()` to call analysis before generation
  - Added CSS for `.message-triggers` and `.modal-triggers-section`
  - Updated JavaScript to display trigger info in modal

## Future Enhancements

Possible improvements:
1. Add links to the trigger source code
2. Show condition function docstrings
3. Visualize the full state machine graph
4. Detect and warn about messages with no triggers
5. Compare expected vs. actual triggers from tests

## Testing

To verify the feature works:

1. Generate previews: `python manage.py preview_all_messages --module activities --languages en`
2. Open `/static/email_previews/index_all.html` or use multi-tenant URL
3. Look for "🎯 Triggered by:" sections in the gallery
4. Click any message to open the modal - trigger info should appear below the subject

## Found Triggers

The system currently finds trigger information for **74 different message classes** including:
- Activity lifecycle messages
- Participant notifications
- Funding/donation messages
- Registration confirmations
- Time-based activity updates
- Grant application notices
- And more...


