# Deed Lifecycle Documentation

This document describes the finite state machine (FSM) implementation for Deeds and DeedParticipants, including all states, transitions, triggers, and effects.

## Table of Contents
1. [Deed State Machine](#deed-state-machine)
2. [DeedParticipant State Machine](#deedparticipant-state-machine)
3. [Model Relationships](#model-relationships)
4. [Triggers and Effects](#triggers-and-effects)

---

## Deed State Machine

### Overview
The `DeedStateMachine` extends `ActivityStateMachine` and manages the lifecycle of a Deed activity. Deeds are activities with optional start and end dates where participants can sign up.

### States

#### Inherited States (from ActivityStateMachine)
| State | Value | Description |
|-------|-------|-------------|
| **draft** | `draft` | The activity has been created, but not yet completed. An activity manager is still editing the activity. |
| **submitted** | `submitted` | The activity has been submitted and is ready to be reviewed. |
| **needs_work** | `needs_work` | The activity needs changes before it can be approved. |
| **rejected** | `rejected` | The activity does not fit the programme or does not comply with the rules. The activity does not appear on the platform, but counts in the report. |
| **deleted** | `deleted` | The activity has been removed. The activity does not appear on the platform and does not count in the report. |
| **cancelled** | `cancelled` | The activity is not executed. The activity does not appear on the platform, but counts in the report. |
| **expired** | `expired` | The activity has ended, but did not have any contributions. The activity does not appear on the platform, but counts in the report. |
| **open** | `open` | The activity is accepting new contributions. |
| **succeeded** | `succeeded` | The activity has ended successfully. |

### Transitions

#### Inherited Transitions (from ActivityStateMachine)

##### 1. **initiate**
- **From:** EmptyState
- **To:** draft
- **Type:** Automatic
- **Description:** The activity will be created.

##### 2. **submit**
- **From:** draft, needs_work
- **To:** submitted
- **Type:** Manual
- **Permission:** is_owner
- **Conditions:**
  - is_complete
  - is_valid
  - can_submit
- **Description:** The activity will be submitted for review.

##### 3. **auto_submit**
- **From:** draft, needs_work
- **To:** submitted
- **Type:** Automatic
- **Conditions:**
  - is_complete
  - is_valid
- **Description:** The activity will be submitted for review.

##### 4. **reject**
- **From:** draft, needs_work, submitted
- **To:** rejected
- **Type:** Manual
- **Permission:** is_staff
- **Description:** Reject if the activity does not align with your program or guidelines.

##### 5. **publish**
- **From:** submitted, draft, needs_work
- **To:** open
- **Type:** Manual
- **Permission:** is_owner
- **Conditions:**
  - is_complete
  - is_valid
  - can_publish
- **Description:** Your activity will be open to contributions.

##### 6. **auto_publish**
- **From:** submitted, draft, needs_work
- **To:** open
- **Type:** Automatic
- **Conditions:**
  - is_complete
  - is_valid
  - should_auto_approve
- **Description:** Automatically publish activity when initiative is approved.

##### 7. **auto_approve**
- **From:** submitted, rejected
- **To:** open
- **Type:** Automatic
- **Conditions:**
  - is_complete
  - is_valid
  - should_auto_approve
- **Description:** The activity will be visible in the frontend and people can apply to the activity.

##### 8. **approve**
- **From:** submitted, needs_work, draft
- **To:** open
- **Type:** Manual
- **Permission:** is_staff
- **Conditions:**
  - is_complete
  - is_valid
  - should_auto_approve
- **Description:** The activity will be published and visible in the frontend for people to contribute to.

##### 9. **request_changes**
- **From:** submitted
- **To:** needs_work
- **Type:** Manual
- **Permission:** is_staff
- **Description:** The activity needs changes before it can be approved.

##### 10. **restore**
- **From:** rejected, cancelled, deleted, expired
- **To:** needs_work
- **Type:** Manual
- **Permission:** is_owner
- **Description:** The activity status is changed to 'Needs work'. Then you can make changes to the activity and submit it again.

##### 11. **delete**
- **From:** draft, needs_work
- **To:** deleted
- **Type:** Manual
- **Permission:** is_owner
- **Description:** Delete the activity if you do not want it to be included in the report.

#### Deed-Specific Transitions

##### 12. **succeed**
- **From:** open, expired
- **To:** succeeded
- **Type:** Automatic
- **Conditions:**
  - can_succeed (has participants)
- **Description:** The activity ends successfully.
- **Effects:**
  - Transition all participants to succeeded (if not started)
  - Send ActivitySucceededNotification
  - Set end date if not already set

##### 13. **expire**
- **From:** open, submitted, succeeded
- **To:** expired
- **Type:** Automatic
- **Description:** The activity will be cancelled because no one has signed up for the registration deadline.
- **Effects:**
  - Fail organizer
  - Send ActivityExpiredNotification

##### 14. **succeed_manually**
- **From:** open
- **To:** succeeded
- **Type:** Manual
- **Permission:** is_owner
- **Conditions:**
  - has_no_end_date
  - can_succeed (has participants)
- **Description:** The activity ends and people can no longer register.

##### 15. **reopen**
- **From:** expired, succeeded
- **To:** open
- **Type:** Automatic
- **Description:** Reopen the activity.
- **Effects:**
  - Re-accept participants (if not finished)

##### 16. **reopen_manually**
- **From:** succeeded, expired
- **To:** draft
- **Type:** Manual
- **Permission:** is_owner
- **Description:** The activity will be set to the status 'Needs work'. Then you can make changes to the activity and submit it again.

##### 17. **cancel**
- **From:** open, succeeded
- **To:** cancelled
- **Type:** Manual
- **Permission:** is_owner
- **Description:** Cancel if the activity will not be executed. An activity manager can no longer edit the activity and it will no longer be visible on the platform.
- **Effects:**
  - Fail organizer
  - Send ActivityCancelledNotification

---

## DeedParticipant State Machine

### Overview
The `DeedParticipantStateMachine` extends `ContributorStateMachine` and manages the lifecycle of participants in a Deed activity.

### States

#### Inherited States (from ContributorStateMachine)
| State | Value | Description |
|-------|-------|-------------|
| **new** | `new` | The user started a contribution |
| **succeeded** | `succeeded` | The contribution was successful. |
| **failed** | `failed` | The contribution failed. |

#### DeedParticipant-Specific States
| State | Value | Description |
|-------|-------|-------------|
| **accepted** | `accepted` | This person has been signed up for the activity and was accepted automatically. |
| **withdrawn** | `withdrawn` | This person has withdrawn. |
| **rejected** | `rejected` | This person has been removed from the activity. |

### Transitions

#### 1. **initiate**
- **From:** EmptyState
- **To:** accepted
- **Type:** Automatic
- **Description:** The contribution was created.
- **Effects:**
  - Succeed immediately if activity already started
  - Create EffortContribution
  - Send NewParticipantNotification (if user joins themselves)
  - Send ParticipantAddedNotification (if added by manager, user is active)
  - Send InactiveParticipantAddedNotification (if added by manager, user is inactive)
  - Send ManagerParticipantAddedOwnerNotification (if added by manager, not owner)
  - Send ParticipantJoinedNotification (if user joins themselves)
  - Follow activity

#### 2. **succeed**
- **From:** accepted
- **To:** succeeded
- **Type:** Automatic
- **Description:** The contribution was successful.
- **Effects:**
  - Succeed activity if it's finished
  - Succeed effort contributions

#### 3. **re_accept**
- **From:** succeeded
- **To:** accepted
- **Type:** Automatic
- **Description:** Put a participant back as participating after it was successful.
- **Effects:**
  - Reset effort contributions
  - Follow activity

#### 4. **withdraw**
- **From:** succeeded, accepted
- **To:** withdrawn
- **Type:** Manual
- **Permission:** is_user (the participant themselves)
- **Description:** Stop your participation in the activity.
- **Effects:**
  - Fail effort contributions
  - Send ParticipantWithdrewNotification
  - Send ParticipantWithdrewConfirmationNotification
  - Unfollow activity

#### 5. **reapply**
- **From:** withdrawn
- **To:** accepted
- **Type:** Manual
- **Permission:** is_user (the participant themselves)
- **Conditions:**
  - activity_is_open
- **Description:** Reapply after previously withdrawing.
- **Effects:**
  - Reset effort contributions
  - Succeed immediately if activity already started
  - Follow activity

#### 6. **remove**
- **From:** accepted, succeeded
- **To:** rejected
- **Type:** Manual
- **Permission:** is_owner (activity owner or staff)
- **Description:** Remove participant from the activity.
- **Effects:**
  - Expire activity if finished and will be empty
  - Fail effort contributions
  - Send ParticipantRemovedOwnerNotification (if removed by non-owner)
  - Send ParticipantRemovedNotification (if removed by non-owner)
  - Unfollow activity

#### 7. **accept**
- **From:** rejected, withdrawn
- **To:** accepted
- **Type:** Manual
- **Permission:** is_owner (activity owner or staff)
- **Description:** Reaccept user after previously withdrawing or rejecting.
- **Effects:**
  - Succeed immediately if activity already started
  - Succeed activity if finished and was expired

---

## Model Relationships

### Deed Model
```python
class Deed(Activity):
    start = DateField(blank=True, null=True)
    end = DateField(blank=True, null=True)
    enable_impact = BooleanField(default=False)
    target = IntegerField(blank=True, null=True)
```

**Key Properties:**
- `participants`: Returns contributors with status 'accepted' or 'succeeded'
- `efforts`: Returns all EffortContribution objects for the deed
- `realized`: Count of succeeded effort contributions

### DeedParticipant Model
```python
class DeedParticipant(Contributor):
    # Inherits user, activity, status from Contributor
```

**Relationships:**
- Belongs to a Deed (activity)
- Has a User
- Has EffortContribution(s)

---

## Triggers and Effects

### Deed Triggers

#### 1. **ModelChangedTrigger: 'end' field**
Triggered when the end date changes.

**Effects:**
- **TransitionEffect(DeedStateMachine.reopen)** - Conditions: is_not_finished
- **TransitionEffect(DeedStateMachine.succeed)** - Conditions: is_finished AND has_participants
- **TransitionEffect(DeedStateMachine.expire)** - Conditions: is_finished AND has_no_participants
- **RescheduleEffortsEffect** - Reschedule all effort contributions
- **NotificationEffect(DeedDateChangedNotification)** - Conditions: is_not_finished

#### 2. **ModelChangedTrigger: 'start' field**
Triggered when the start date changes.

**Effects:**
- **RelatedTransitionEffect('participants', DeedParticipantStateMachine.re_accept)** - Conditions: has_start_date AND is_not_started
- **RelatedTransitionEffect('participants', DeedParticipantStateMachine.succeed)** - Conditions: is_started
- **RescheduleEffortsEffect** - Reschedule all effort contributions
- **NotificationEffect(DeedDateChangedNotification)** - Conditions: is_not_started

#### 3. **ModelChangedTrigger: 'target' field**
Triggered when the target number of participants changes.

**Effects:**
- **UpdateImpactGoalsForActivityEffect** - Update impact goals

#### 4. **TransitionTrigger: DeedStateMachine.auto_approve**
Triggered when deed is auto-approved.

**Effects:**
- **TransitionEffect(DeedStateMachine.reopen)** - Conditions: is_not_finished
- **TransitionEffect(DeedStateMachine.succeed)** - Conditions: is_finished AND has_participants
- **TransitionEffect(DeedStateMachine.expire)** - Conditions: is_finished AND has_no_participants

#### 5. **TransitionTrigger: DeedStateMachine.publish**
Triggered when deed is published.

**Effects:**
- **TransitionEffect(DeedStateMachine.reopen)** - Conditions: is_not_finished
- **TransitionEffect(DeedStateMachine.succeed)** - Conditions: is_finished AND has_participants
- **TransitionEffect(DeedStateMachine.expire)** - Conditions: is_finished AND has_no_participants
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed)** - Conditions: has_organizer

#### 6. **TransitionTrigger: DeedStateMachine.reopen**
Triggered when deed is reopened.

**Effects:**
- **RelatedTransitionEffect('participants', DeedParticipantStateMachine.re_accept)** - Conditions: is_not_finished

#### 7. **TransitionTrigger: DeedStateMachine.succeed**
Triggered when deed succeeds.

**Effects:**
- **RelatedTransitionEffect('participants', DeedParticipantStateMachine.succeed)** - Conditions: is_not_started
- **NotificationEffect(ActivitySucceededNotification)**
- **SetEndDateEffect** - Set end date to today if not set

#### 8. **TransitionTrigger: DeedStateMachine.expire**
Triggered when deed expires.

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
- **NotificationEffect(ActivityExpiredNotification)**

#### 9. **TransitionTrigger: DeedStateMachine.reject**
Triggered when deed is rejected.

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
- **NotificationEffect(ActivityRejectedNotification)**

#### 10. **TransitionTrigger: DeedStateMachine.cancel**
Triggered when deed is cancelled.

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)**
- **NotificationEffect(ActivityCancelledNotification)**

#### 11. **TransitionTrigger: DeedStateMachine.restore**
Triggered when deed is restored.

**Effects:**
- **RelatedTransitionEffect('organizer', OrganizerStateMachine.reset)**
- **NotificationEffect(ActivityRestoredNotification)**

### DeedParticipant Triggers

#### 1. **TransitionTrigger: DeedParticipantStateMachine.initiate**
Triggered when a participant is created.

**Effects:**
- **TransitionEffect(DeedParticipantStateMachine.succeed)** - Conditions: activity_did_start
- **CreateEffortContribution** - Create effort contribution record
- **NotificationEffect(NewParticipantNotification)** - Conditions: is_user
- **NotificationEffect(ParticipantAddedNotification)** - Conditions: is_not_user AND participant_is_active
- **NotificationEffect(InactiveParticipantAddedNotification)** - Conditions: is_not_user AND participant_is_inactive
- **NotificationEffect(ManagerParticipantAddedOwnerNotification)** - Conditions: is_not_user AND is_not_owner
- **NotificationEffect(ParticipantJoinedNotification)** - Conditions: is_user
- **FollowActivityEffect** - User follows the activity

#### 2. **TransitionTrigger: DeedParticipantStateMachine.remove**
Triggered when a participant is removed.

**Effects:**
- **RelatedTransitionEffect('activity', DeedStateMachine.expire)** - Conditions: activity_is_finished AND activity_will_be_empty
- **RelatedTransitionEffect('contributions', EffortContributionStateMachine.fail)**
- **NotificationEffect(ParticipantRemovedOwnerNotification)** - Conditions: is_not_owner
- **NotificationEffect(ParticipantRemovedNotification)** - Conditions: is_not_owner
- **UnFollowActivityEffect** - User unfollows the activity

#### 3. **TransitionTrigger: DeedParticipantStateMachine.succeed**
Triggered when a participant succeeds.

**Effects:**
- **RelatedTransitionEffect('activity', DeedStateMachine.succeed)** - Conditions: activity_is_finished
- **RelatedTransitionEffect('contributions', EffortContributionStateMachine.succeed)** - Conditions: contributor_is_active
- **RelatedTransitionEffect('contributions', EffortContributionStateMachine.succeed)** - (duplicate in code)

#### 4. **TransitionTrigger: DeedParticipantStateMachine.accept**
Triggered when a participant is accepted (after rejection/withdrawal).

**Effects:**
- **TransitionEffect(DeedParticipantStateMachine.succeed)** - Conditions: activity_did_start
- **RelatedTransitionEffect('activity', DeedStateMachine.succeed)** - Conditions: activity_is_finished AND activity_expired

#### 5. **TransitionTrigger: DeedParticipantStateMachine.re_accept**
Triggered when a participant is re-accepted.

**Effects:**
- **RelatedTransitionEffect('contributions', EffortContributionStateMachine.reset)**
- **FollowActivityEffect** - User follows the activity

#### 6. **TransitionTrigger: DeedParticipantStateMachine.withdraw**
Triggered when a participant withdraws.

**Effects:**
- **RelatedTransitionEffect('contributions', EffortContributionStateMachine.fail)**
- **NotificationEffect(ParticipantWithdrewNotification)**
- **NotificationEffect(ParticipantWithdrewConfirmationNotification)**
- **UnFollowActivityEffect** - User unfollows the activity

#### 7. **TransitionTrigger: DeedParticipantStateMachine.reapply**
Triggered when a participant reapplies after withdrawal.

**Effects:**
- **RelatedTransitionEffect('contributions', EffortContributionStateMachine.reset)**
- **TransitionEffect(DeedParticipantStateMachine.succeed)** - Conditions: activity_did_start
- **FollowActivityEffect** - User follows the activity

---

## Condition Functions

### Deed Conditions

| Condition | Description |
|-----------|-------------|
| `has_no_end_date()` | Deed has no end date set |
| `can_succeed()` | Deed has at least one participant |
| `is_started()` | Start date is in the past |
| `is_not_started()` | Start date is not in the past or not set |
| `is_finished()` | End date is in the past |
| `is_not_finished()` | End date is not in the past or not set |
| `has_participants()` | Deed has at least one participant |
| `has_no_participants()` | Deed has no participants |
| `has_no_start_date()` | Deed has no start date set |
| `has_start_date()` | Deed has a start date set |

### DeedParticipant Conditions

| Condition | Description |
|-----------|-------------|
| `is_user(user)` | User is the participant |
| `is_owner(user)` | User is the activity owner, staff, or superuser |
| `activity_is_open()` | Activity status is 'open' |
| `activity_is_finished()` | Activity end date is in the past |
| `activity_expired()` | Activity status is 'expired' |
| `activity_not_expired()` | Activity status is not 'expired' |
| `activity_did_start()` | Activity start date is in the past or not set |
| `activity_will_be_empty()` | Only one participant remaining |
| `activity_has_no_end()` | Activity has no end date |
| `contributor_is_active()` | Contributor status is 'new' |
| `participant_is_active()` | User account is active and platform is open |
| `participant_is_inactive()` | User account is inactive or platform is closed |

---

## Lifecycle Diagrams

### Deed Lifecycle Flow

```
[Create] → draft
    ↓
    ├─[submit]─→ submitted ─┬─[approve]─────→ open
    │                       ├─[reject]──────→ rejected
    │                       └─[request_changes]→ needs_work
    │                                              ↓
    ├─[publish]──────────────────────────────────┘
    │
    └─[delete]──→ deleted

open ──┬─[succeed]──→ succeeded
       ├─[expire]───→ expired
       ├─[cancel]───→ cancelled
       └─[reopen]←──┐
                     │
succeeded/expired/cancelled/rejected/deleted
       └─[restore]──→ needs_work
```

### DeedParticipant Lifecycle Flow

```
[Create] → accepted
    ↓
    ├─[succeed (auto)]───→ succeeded
    │                         ↓
    │                    [re_accept]
    │                         ↓
    ├─[withdraw]────→ withdrawn ─[reapply]→ accepted
    │
    └─[remove]──────→ rejected ──[accept]─→ accepted
```

---

## Key Behaviors

### Automatic Transitions

1. **When a deed is published/approved:**
   - If the end date has passed and there are participants → succeed
   - If the end date has passed and there are no participants → expire
   - If the end date hasn't passed → stay open/reopen

2. **When the start date changes:**
   - If start date is now in the past → all participants succeed
   - If start date is moved to future → participants re-accept

3. **When the end date changes:**
   - If end date is now in the past and has participants → deed succeeds
   - If end date is now in the past and no participants → deed expires
   - If end date is moved to future → deed reopens

4. **When a participant joins:**
   - If the activity already started → participant immediately succeeds
   - Otherwise → participant is in 'accepted' state

5. **When the last participant is removed:**
   - If the activity has finished → deed expires

### Notifications

**Activity Manager Notifications:**
- ActivitySucceededNotification (deed succeeds)
- ActivityExpiredNotification (deed expires)
- ActivityRejectedNotification (deed rejected)
- ActivityCancelledNotification (deed cancelled)
- ActivityRestoredNotification (deed restored)
- DeedDateChangedNotification (start/end date changes)
- ParticipantRemovedOwnerNotification (participant removed by manager)
- ManagerParticipantAddedOwnerNotification (participant added by manager)

**Participant Notifications:**
- NewParticipantNotification (participant joins themselves)
- ParticipantAddedNotification (participant added by manager, active user)
- InactiveParticipantAddedNotification (participant added by manager, inactive user)
- ParticipantJoinedNotification (participant joins themselves)
- ParticipantWithdrewNotification (participant withdraws)
- ParticipantWithdrewConfirmationNotification (participant withdraws confirmation)
- ParticipantRemovedNotification (participant removed by manager)

---

## Implementation Files

- **States:** `bluebottle/deeds/states.py`
- **Triggers:** `bluebottle/deeds/triggers.py`
- **Models:** `bluebottle/deeds/models.py`
- **Base Activity States:** `bluebottle/activities/states.py`
- **Base Activity Triggers:** `bluebottle/activities/triggers.py`

---

*Generated: 2025-10-30*

