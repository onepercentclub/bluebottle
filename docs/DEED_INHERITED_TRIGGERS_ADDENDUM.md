# Deed Inherited Triggers & Effects - Addendum

## ⚠️ Important: Inherited Behavior

This document supplements the main `DEED_LIFECYCLE.md` documentation with **inherited triggers and effects** from base classes that were not fully documented in the HTML visualization.

The `DeedTriggers` class extends `ActivityTriggers`, which means **all Deed activities inherit these additional triggers and effects** beyond what's specific to Deeds.

---

## Inherited from ActivityTriggers

### 1. TransitionTrigger: ActivityStateMachine.initiate
**When:** A new Deed is created

**Effects:**
- **CreateOrganizer** - Automatically create an Organizer object for the activity owner
- **CopyCategories** - Copy categories from the initiative if applicable

**Impact:** Every Deed gets an associated Organizer when created.

---

### 2. TransitionTrigger: ActivityStateMachine.submit
**When:** Deed is submitted for review (manual)

**Effects:**
- **TransitionEffect(auto_approve)** 
  - Condition: `should_approve_instantly` - If reviewing is disabled or initiative already approved
  - Automatically approves the deed immediately
  
- **NotificationEffect: ActivitySubmittedReviewerNotification**
  - Condition: `should_review` - If reviewing is enabled
  - Recipient: Platform reviewers/staff
  - Purpose: Notify reviewers that a new deed needs review
  
- **NotificationEffect: ActivitySubmittedNotification**
  - Subject: "You submitted an activity on {site_name}"
  - Condition: `should_review AND is_not_funding`
  - Recipient: Activity owner
  - Purpose: Confirm submission to the owner

**Impact:** Submission may trigger automatic approval and notifies both owner and reviewers.

---

### 3. TransitionTrigger: ActivityStateMachine.auto_submit
**When:** Deed is automatically submitted

**Effects:**
- **TransitionEffect(auto_approve)**
  - Condition: `should_approve_instantly`
  - Automatically approves if conditions met

**Impact:** Auto-submitted deeds can immediately become approved/open.

---

### 4. TransitionTrigger: ActivityStateMachine.approve
**When:** Staff approves a submitted deed

**Effects:**
- **NotificationEffect: ActivityApprovedNotification**
  - Subject: "Your activity on {site_name} has been approved!"
  - Condition: `is_not_funding`
  - Recipient: Activity owner
  
- **NotificationEffect: TermsOfServiceNotification**
  - Subject: "Terms of service"
  - Condition: `should_mail_tos` - If platform settings enable ToS mailing
  - Recipient: Activity owner
  - Purpose: Send terms of service agreement

**Impact:** Approval notifies owner and optionally sends ToS.

---

### 5. TransitionTrigger: ActivityStateMachine.request_changes
**When:** Staff requests changes to a submitted deed

**Effects:**
- **NotificationEffect: ActivityNeedsWorkNotification**
  - Subject: "The activity you submitted on {site_name} needs work"
  - Condition: `is_not_funding`
  - Recipient: Activity owner

**Impact:** Owner is notified their deed needs changes before approval.

---

### 6. TransitionTrigger: ActivityStateMachine.reject
**When:** Staff rejects a deed

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
  - Condition: `has_organizer`
  - Fails the organizer when deed is rejected

**Impact:** Rejection cascades to fail the organizer contributor.

---

### 7. TransitionTrigger: ActivityStateMachine.auto_approve
**When:** Deed is auto-approved (after submit or when initiative approved)

**Effects:**
- **SetPublishedDateEffect** - Sets the `published` timestamp
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed)**
  - Condition: `has_organizer`
  - Marks the organizer as succeeded

**Impact:** Auto-approval publishes the deed and succeeds the organizer.

---

### 8. TransitionTrigger: ActivityStateMachine.publish
**When:** Owner manually publishes a deed

**Effects:**
- **SetPublishedDateEffect** - Sets the `published` timestamp
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed)**
  - Condition: `has_organizer`
  - Marks the organizer as succeeded
  
- **NotificationEffect: ActivityPublishedReviewerNotification**
  - Recipient: Platform reviewers/staff
  - Purpose: Inform reviewers that activity was published
  
- **NotificationEffect: ActivityPublishedNotification**
  - Subject: "Your activity on {site_name} has been published!"
  - Recipient: Activity owner
  - Purpose: Confirm publication to owner

**Impact:** Publishing sets timestamps, succeeds organizer, and notifies both owner and reviewers.

---

### 9. TransitionTrigger: ActivityStateMachine.cancel
**When:** Owner or staff cancels a deed

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
  - Condition: `has_organizer`
  - Fails the organizer when deed is cancelled

**Impact:** Cancellation fails the organizer.

---

### 10. TransitionTrigger: ActivityStateMachine.expire
**When:** Deed expires (automatic)

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
  - Condition: `has_organizer`
  - Fails the organizer when deed expires

**Impact:** Expiration fails the organizer.

---

### 11. TransitionTrigger: ActivityStateMachine.restore
**When:** Deed is restored from rejected/cancelled/expired/deleted state

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.reset)**
  - Condition: `has_organizer`
  - Resets the organizer back to 'new' state

**Impact:** Restoring the deed resets the organizer to allow re-attempt.

---

### 12. TransitionTrigger: ActivityStateMachine.delete
**When:** Owner deletes a deed in draft/needs_work state

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
  - Condition: `has_organizer`
  - Fails the organizer when deed is deleted

**Impact:** Deletion fails the organizer.

---

## Inherited from ContributorTriggers

### 1. ModelDeletedTrigger (for DeedParticipant)
**When:** A DeedParticipant is deleted from the database

**Effects:**
- **DeleteRelatedContributionsEffect** - Cascades deletion to all related contribution objects

**Impact:** Deleting a participant cleans up their contribution records.

---

## Summary of Additional Notifications

Beyond the deed-specific notifications documented in the main lifecycle doc, these **inherited notifications** also apply:

### To Activity Owner (5 additional):
1. **ActivitySubmittedNotification** - "You submitted an activity on {site_name}"
2. **ActivityApprovedNotification** - "Your activity on {site_name} has been approved!"
3. **ActivityNeedsWorkNotification** - "The activity you submitted on {site_name} needs work"
4. **ActivityPublishedNotification** - "Your activity on {site_name} has been published!"
5. **TermsOfServiceNotification** - "Terms of service" (conditional)

### To Reviewers/Staff (2 additional):
1. **ActivitySubmittedReviewerNotification** - Deed submitted for review
2. **ActivityPublishedReviewerNotification** - Deed was published

---

## Key Condition Functions (Inherited)

### should_approve_instantly(effect)
- Returns `True` if:
  - Reviewing is disabled in platform settings, OR
  - The deed's initiative is already approved
- Used to determine if deed should skip review process

### should_review(effect)
- Returns `True` if:
  - Reviewing is enabled in platform settings, OR
  - The deed's initiative is not yet approved
- Used to determine if deed needs manual review

### is_not_funding(effect)
- Returns `True` if the activity is not a Funding activity
- Used to filter notifications specific to non-funding activities (like Deeds)

### has_organizer(effect)
- Returns `True` if the activity has an organizer object
- Used to conditionally trigger organizer state changes

### should_mail_tos(effect)
- Returns `True` if platform settings have "mail_terms_of_service" enabled
- Used to determine if ToS email should be sent

---

## Impact on State Diagrams

### Enhanced Submit Flow:
```
draft → [submit] → submitted
                     ↓
            [if should_review]
                     ↓
            Send notifications to:
              - Owner (confirmation)
              - Reviewers (action needed)
                     ↓
            [if should_approve_instantly]
                     ↓
                  [auto_approve]
                     ↓
                    open
```

### Enhanced Publish Flow:
```
draft/submitted → [publish] → open
                               ↓
                      Set published date
                               ↓
                      Succeed organizer
                               ↓
                      Send notifications to:
                        - Owner (confirmation)
                        - Reviewers (info)
```

### Organizer Lifecycle (Related):
```
[Deed initiate] → Create organizer (new state)
                        ↓
[Deed publish/approve] → Organizer succeeds
                        ↓
[Deed cancel/expire/delete/reject] → Organizer fails
                        ↓
[Deed restore] → Organizer resets to new
```

---

## Why This Matters

### For Developers:
- **Organizer objects** are automatically created for every Deed
- **Automatic approval** can bypass the review process based on settings
- **Multiple notification paths** exist depending on platform configuration
- **Organizer state** is tightly coupled to activity state

### For Product/QA:
- Activities may **skip submission** if reviewing is disabled
- **ToS emails** are conditionally sent based on platform settings
- **Reviewers receive notifications** when deeds are submitted
- **Organizer contributors** track the activity owner's success/failure

### For Testing:
- Test with **reviewing enabled/disabled** to see different flows
- Verify **organizer creation** on deed creation
- Check **reviewer notifications** are sent appropriately
- Validate **organizer state changes** cascade correctly

---

## Integration with Deed-Specific Triggers

The **DeedTriggers** class uses:
```python
class DeedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        # Deed-specific triggers here
    ]
```

This means:
- ✅ All ActivityTriggers execute first
- ✅ Then Deed-specific triggers execute
- ✅ Both sets of effects are applied
- ✅ Conditions are evaluated for each trigger

Example: When a deed is published:
1. **ActivityTriggers.publish** runs:
   - Sets published date
   - Succeeds organizer
   - Sends owner/reviewer notifications
2. **DeedTriggers.publish** runs:
   - Conditionally reopens if not finished
   - Conditionally succeeds if finished with participants
   - Conditionally expires if finished without participants

---

## Complete Notification List for Deeds

### Activity Owner Receives:
From ActivityTriggers:
1. ActivitySubmittedNotification
2. ActivityApprovedNotification
3. ActivityNeedsWorkNotification
4. ActivityPublishedNotification
5. TermsOfServiceNotification (conditional)

From DeedTriggers:
6. ActivitySucceededNotification
7. ActivityExpiredNotification
8. ActivityRejectedNotification
9. ActivityCancelledNotification
10. ActivityRestoredNotification
11. DeedDateChangedNotification

**Total: Up to 11 different notifications**

### Platform Reviewers/Staff Receive:
1. ActivitySubmittedReviewerNotification
2. ActivityPublishedReviewerNotification

### Participants Receive:
(From DeedParticipantTriggers)
1. NewParticipantNotification
2. ParticipantAddedNotification
3. InactiveParticipantAddedNotification
4. ManagerParticipantAddedOwnerNotification
5. ParticipantJoinedNotification
6. ParticipantWithdrewNotification
7. ParticipantWithdrewConfirmationNotification
8. ParticipantRemovedNotification
9. ParticipantRemovedOwnerNotification

**Total: 9 participant notifications**

---

## Files Referenced

- **Base Triggers:** `bluebottle/activities/triggers.py` (lines 70-214)
- **Deed Triggers:** `bluebottle/deeds/triggers.py`
- **Base Messages:** `bluebottle/activities/messages/activity_manager.py`
- **Reviewer Messages:** `bluebottle/activities/messages/reviewer.py`
- **Deed Messages:** `bluebottle/deeds/messages.py`

---

**Generated:** October 30, 2025  
**Status:** Supplemental documentation to DEED_LIFECYCLE.md  
**Purpose:** Document inherited behavior from base classes

