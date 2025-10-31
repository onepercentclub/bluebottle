# Deed & DeedParticipant State Machine Visualization

An interactive HTML visualization of the Deed and DeedParticipant finite state machines, including all states, transitions, effects, conditions, and notifications.

## 📁 Contents

This directory contains:

### Main Files
- **index.html** - Main navigation page with overview of all states
- **state_styles.css** - Stylesheet for all visualization pages

### Deed State Pages (9 states)
- deed_draft.html
- deed_submitted.html
- deed_needs_work.html
- deed_open.html
- deed_succeeded.html
- deed_expired.html
- deed_cancelled.html
- deed_rejected.html
- deed_deleted.html

### DeedParticipant State Pages (6 states)
- participant_accepted.html
- participant_succeeded.html
- participant_withdrawn.html
- participant_rejected.html
- participant_new.html
- participant_failed.html

## 🚀 Usage

1. Open `index.html` in any web browser
2. Browse through the state overview
3. Click on any state to see:
   - All outgoing transitions (with clickable links to target states)
   - All incoming transitions (with clickable links to source states)
   - Transition types (Manual vs Automatic)
   - Required permissions
   - Conditions that must be met
   - Effects that are triggered
   - Notifications sent (with subject and recipient)
   - Model change triggers

## 🎨 Features

### Visual Elements
- **Color-coded states** - Different colors for draft, active, success, and terminal states
- **Transition badges** - Manual vs Automatic transitions clearly marked
- **Clickable navigation** - All state references are clickable links
- **Responsive design** - Works on desktop, tablet, and mobile

### Information Displayed

#### For Each Transition:
- ✅ **Conditions** - What must be true for the transition to occur
- 🔐 **Permissions** - Who can trigger the transition
- ⚡ **Effects** - What happens when the transition occurs
- 📧 **Notifications** - Email notifications sent with subject and recipient

#### For Each State:
- 📤 **Outgoing transitions** - Where you can go from this state
- 📥 **Incoming transitions** - How you get to this state
- 🎯 **Triggers** - Model change triggers (e.g., when start/end date changes)

## 📊 State Machine Overview

### Deed States
The Deed lifecycle follows this general pattern:
```
draft → submitted → needs_work (optional)
                 ↓
               open → succeeded ✓
                   → expired ✗
                   → cancelled ✗
```

### DeedParticipant States
Participant lifecycle:
```
Create → accepted → succeeded ✓
            ↓
         withdrawn (by user)
            ↓
         rejected (by owner)
```

## 🛠️ Generated From

These pages were auto-generated from:
- `bluebottle/deeds/states.py` - State machine definitions
- `bluebottle/deeds/triggers.py` - Trigger and effect definitions
- `bluebottle/deeds/messages.py` - Notification messages
- `bluebottle/activities/states.py` - Base state machines
- `bluebottle/activities/messages/` - Base notification messages

## 📝 Key Concepts

### Automatic vs Manual Transitions
- **Automatic** - Triggered by the system when conditions are met
- **Manual** - Must be explicitly triggered by a user with proper permissions

### Permissions
- **is_owner** - Activity owner, staff, or superuser
- **is_staff** - Staff member or superuser
- **is_user** - The participant themselves

### Common Conditions
- `is_complete()` - All required fields filled
- `is_valid()` - All fields pass validation
- `is_finished()` - End date is in the past
- `has_participants()` - At least one participant signed up
- `activity_is_open()` - Activity is in 'open' state

### Effect Types
- **TransitionEffect** - Trigger another transition
- **RelatedTransitionEffect** - Trigger transitions on related objects
- **NotificationEffect** - Send email notification
- **ModelEffect** - Modify model data (e.g., SetEndDateEffect)

## 🔄 Regenerating

To regenerate these pages after code changes:

```bash
# Generate Deed state pages
python3 generate_deed_state_pages.py

# Generate DeedParticipant state pages
python3 generate_participant_state_pages.py
```

## 📅 Generated

Last generated: October 30, 2025

---

For questions or issues, please refer to the source code in `bluebottle/deeds/`

