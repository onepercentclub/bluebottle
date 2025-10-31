# Bluebottle Platform - State Machines Overview

## Summary

The Bluebottle platform uses **finite state machines (FSM)** to manage the lifecycle of activities, participants, and related entities. This document provides an overview of all state machines in the system.

## Documentation Status

### ✅ Completed
- **Deeds** - Full HTML visualization with all states, transitions, triggers, and effects
  - `deed_states_visualization/` directory with 16 HTML pages
  - Comprehensive markdown documentation in `DEED_LIFECYCLE.md`
  - Inherited triggers documented in `DEED_INHERITED_TRIGGERS_ADDENDUM.md`

### ⏳ Pending Documentation

## Activity Types (6 groups, 11 models)

### 1. Time-Based Activities ⭐ Most Complex
**Description:** Activities with dates, deadlines, or schedules where volunteers contribute their time

**Models:**
- `DateActivity` - Activities on specific dates
- `DeadlineActivity` - Activities with deadlines
- `ScheduleActivity` - Activities with flexible schedules
- `PeriodicActivity` - Recurring activities
- `PeriodActivity` - Activities during a period

**Files:**
- States: `bluebottle/time_based/states/states.py`
- Triggers: `bluebottle/time_based/triggers/activities.py`
- Messages: `bluebottle/time_based/messages.py`

**State Machine Classes:**
- `TimeBasedStateMachine` (base)
- `DateStateMachine`
- `RegistrationActivityStateMachine`
- `DeadlineActivityStateMachine`
- `ScheduleActivityStateMachine`
- `PeriodicActivityStateMachine`
- `RegisteredDateActivityStateMachine`

---

### 2. Funding/Crowdfunding ⭐ High Priority
**Description:** Crowdfunding campaigns where people donate money

**Models:**
- `Funding` - Crowdfunding campaign
- `Donor` - Donor contributor

**Files:**
- States: `bluebottle/funding/states.py`
- Triggers: `bluebottle/funding/triggers/funding.py`
- Messages: `bluebottle/funding/messages.py`

**State Machine Classes:**
- `FundingStateMachine`
- `DonorStateMachine`
- `BasePaymentStateMachine`
- `PayoutStateMachine`
- `BankAccountStateMachine`
- `PayoutAccountStateMachine`
- `DonationStateMachine`

**Additional Payment Integrations:**
- Stripe, Flutterwave, Lipisha, Telesom, Vitepay, Pledge

---

### 3. Deeds ✅ COMPLETED
**Description:** Simple activities where people sign up to participate

**Models:**
- `Deed` - Deed activity
- `DeedParticipant` - Deed participant

**Files:**
- States: `bluebottle/deeds/states.py`
- Triggers: `bluebottle/deeds/triggers.py`
- Messages: `bluebottle/deeds/messages.py`

**State Machine Classes:**
- `DeedStateMachine`
- `DeedParticipantStateMachine`

**Documentation:**
- ✅ HTML visualization: `deed_states_visualization/`
- ✅ Markdown docs: `DEED_LIFECYCLE.md`, `DEED_INHERITED_TRIGGERS_ADDENDUM.md`

---

### 4. Collect Activities
**Description:** Activities where people collect and contribute items

**Models:**
- `CollectActivity` - Collection activity
- `CollectContributor` - Collection contributor

**Files:**
- States: `bluebottle/collect/states.py`
- Triggers: `bluebottle/collect/triggers.py`
- Messages: `bluebottle/collect/messages.py`

**State Machine Classes:**
- `CollectActivityStateMachine`
- `CollectContributorStateMachine`
- `CollectContributionStateMachine`

---

### 5. Grant Applications
**Description:** Grant application and management system

**Models:**
- `GrantApplication` - Grant application
- `GrantDonor` - Grant donor

**Files:**
- States: `bluebottle/grant_management/states.py`
- Triggers: `bluebottle/grant_management/triggers.py`

**State Machine Classes:**
- `GrantApplicationStateMachine`
- `GrantDonorStateMachine`
- `GrantPaymentStateMachine`
- `GrantPayoutStateMachine`
- `BankAccountStateMachine`
- `PayoutAccountStateMachine`
- `GrantDepositStateMachine`
- `LedgerItemStateMachine`

---

### 6. Initiatives
**Description:** Parent initiatives that contain activities

**Models:**
- `Initiative` - Initiative/Campaign

**Files:**
- States: `bluebottle/initiatives/states.py`
- Triggers: `bluebottle/initiatives/triggers.py`
- Messages: `bluebottle/initiatives/messages.py`

**State Machine Classes:**
- `ReviewStateMachine`

---

## Participant/Contributor Types (3 groups, 14 models)

### 7. Time-Based Participants ⭐ High Priority
**Description:** Participants in time-based activities

**Models:**
- `DateParticipant` - Date activity participant
- `DeadlineParticipant` - Deadline activity participant
- `ScheduleParticipant` - Schedule activity participant
- `TeamScheduleParticipant` - Team schedule participant
- `PeriodicParticipant` - Periodic activity participant

**Files:**
- States: `bluebottle/time_based/states/participants.py`
- Triggers: `bluebottle/time_based/triggers/participants.py`

**State Machine Classes:**
- `ParticipantStateMachine` (base)
- `RegistrationParticipantStateMachine`
- `DeadlineParticipantStateMachine`
- `RegisteredDateParticipantStateMachine`
- `ScheduleParticipantStateMachine`
- `TeamScheduleParticipantStateMachine`
- `PeriodicParticipantStateMachine`
- `DateParticipantStateMachine`

---

### 8. Teams
**Description:** Team management for team-based activities

**Models:**
- `Team` - Team
- `TeamMember` - Team member

**Files:**
- States: `bluebottle/time_based/states/teams.py`
- Triggers: `bluebottle/time_based/triggers/teams.py`

**State Machine Classes:**
- `TeamStateMachine`
- `TeamMemberStateMachine`

---

### 9. Activity Slots
**Description:** Time slots for scheduled activities

**Models:**
- `Slot` - Activity slot
- `PeriodicSlot` - Periodic slot
- `ScheduleSlot` - Schedule slot
- `TeamScheduleSlot` - Team schedule slot
- `DateActivitySlot` - Date activity slot

**Files:**
- States: `bluebottle/time_based/states/slots.py`
- Triggers: `bluebottle/time_based/triggers/slots.py`

**State Machine Classes:**
- `SlotStateMachine`
- `PeriodicSlotStateMachine`
- `ScheduleSlotStateMachine`
- `TeamScheduleSlotStateMachine`
- `DateActivitySlotStateMachine`

---

## Base/Shared State Machines

### Activity Base Classes
Located in `bluebottle/activities/states.py`:
- `ActivityStateMachine` - Base for all activities
- `ContributorStateMachine` - Base for all contributors/participants
- `ContributionStateMachine` - Base for all contributions
- `OrganizerStateMachine` - Activity organizers
- `EffortContributionStateMachine` - Time-based contributions

### Supporting Classes
- `TimeContributionStateMachine` - Time-based contributions
- `RegistrationStateMachine` - Registration management

---

## Statistics

### Overall Counts
- **Total State Machine Classes:** 72+
- **Total Activity Types:** 6 main groups
- **Total Participant Types:** 3 main groups
- **Total Models with State Machines:** 25+
- **Documented:** 2 (Deed, DeedParticipant)
- **Pending:** 23+

### Priority Levels

#### ⭐⭐⭐ Critical (Most Used)
1. Time-Based Activities (5 models)
2. Time-Based Participants (5 models)
3. Funding & Donor (2 models)

#### ⭐⭐ High Priority
4. Collect Activities (2 models)
5. Teams & Slots (7 models)

#### ⭐ Medium Priority
6. Grant Applications (2 models)
7. Initiatives (1 model)

---

## Documentation Approach

### What We Did for Deeds (Template for Others)

1. **Markdown Documentation** (`DEED_LIFECYCLE.md`)
   - All states with descriptions
   - All transitions with conditions & permissions
   - All triggers with effects
   - All notifications with subjects & recipients
   - Lifecycle diagrams
   - Key behaviors and patterns

2. **Inherited Behavior** (`DEED_INHERITED_TRIGGERS_ADDENDUM.md`)
   - Documented base class triggers
   - Additional notifications
   - Organizer lifecycle
   - Integration patterns

3. **HTML Visualization** (`deed_states_visualization/`)
   - Interactive index page
   - Individual page per state (15 total)
   - Clickable state transitions
   - Color-coded transition types
   - Detailed effects and notifications
   - Professional, condensed styling

4. **Generator Scripts**
   - `generate_deed_state_pages.py`
   - `generate_participant_state_pages.py`
   - Reusable for updates

### Recommended Next Steps

#### Phase 1: Time-Based Activities (Highest Complexity)
Since time-based activities are the most complex with multiple variants:

1. Create `TIME_BASED_LIFECYCLE.md`
2. Document each activity type state machine
3. Document participant state machines
4. Create HTML visualization
5. Generator scripts

**Estimated:** ~300-400 lines of states/transitions to document

#### Phase 2: Funding Activities
1. Create `FUNDING_LIFECYCLE.md`
2. Document Funding and Donor state machines
3. Document payment state machines
4. Create HTML visualization
5. Generator scripts

**Estimated:** ~200-300 lines of states/transitions

#### Phase 3: Collect & Other Activities
1. Create individual lifecycle docs
2. HTML visualizations
3. Generator scripts

**Estimated:** ~100-150 lines each

#### Phase 4: Unified Index
Create a master index page that links to all activity type visualizations:
- `state_machines_visualization/index.html`
- Links to deed, time-based, funding, collect, etc.
- Overview of all activity types
- Search/filter functionality

---

## Files Structure

```
bluebottle/
├── state_machines_visualization/         ← NEW: Master index
│   ├── index.html                        ← Links to all visualizations
│   ├── deed/                             ← Existing (rename from deed_states_visualization)
│   ├── time_based/                       ← NEW
│   ├── funding/                          ← NEW
│   ├── collect/                          ← NEW
│   ├── grants/                           ← NEW
│   ├── initiatives/                      ← NEW
│   └── shared_styles.css                 ← Shared styling
│
├── documentation/                        ← NEW: Markdown docs
│   ├── README.md                         ← Overview
│   ├── DEED_LIFECYCLE.md                 ← Existing
│   ├── TIME_BASED_LIFECYCLE.md           ← NEW
│   ├── FUNDING_LIFECYCLE.md              ← NEW
│   ├── COLLECT_LIFECYCLE.md              ← NEW
│   ├── GRANTS_LIFECYCLE.md               ← NEW
│   └── INITIATIVES_LIFECYCLE.md          ← NEW
│
└── generators/                           ← NEW: Generator scripts
    ├── generate_master_index.py
    ├── generate_deed_states.py           ← Existing
    ├── generate_time_based_states.py     ← NEW
    ├── generate_funding_states.py        ← NEW
    └── ...
```

---

## Complexity Estimates

### Lines of Documentation (Approximate)

| Activity Type | States | Transitions | Triggers | Notifications | Total Lines |
|---------------|--------|-------------|----------|---------------|-------------|
| Deeds (done) | 9 | 17 | 18 | 15 | ~600 |
| Time-Based | 15+ | 30+ | 40+ | 25+ | ~1000 |
| Funding | 12+ | 25+ | 30+ | 20+ | ~800 |
| Collect | 8 | 15 | 20 | 12 | ~500 |
| Grants | 10+ | 20+ | 25+ | 15+ | ~700 |
| Others | 15+ | 30+ | 35+ | 20+ | ~600 |
| **TOTAL** | **69+** | **137+** | **168+** | **107+** | **~4200** |

### Time Estimates

- Markdown documentation: ~2 hours per activity type
- HTML generation scripts: ~3 hours per activity type  
- Testing and refinement: ~1 hour per activity type
- **Total per activity type: ~6 hours**
- **Total for all types: ~30-40 hours**

---

## Benefits of Complete Documentation

### For Developers
- Quick reference for all state transitions
- Understanding of cascade effects
- Clear visibility of notification triggers
- Easier debugging of state-related issues

### For Product Owners
- Complete understanding of user journeys
- Visibility into all notifications sent
- Clear picture of permission requirements
- Documentation of business rules

### For QA/Testing
- Comprehensive test scenarios
- All edge cases documented
- State transition validation
- Notification verification

### For New Team Members
- Self-service learning resource
- Visual state flow understanding
- Complete system behavior documentation
- Reduces onboarding time

---

## Next Action Items

### Immediate (This Session)
- [x] Create overview analysis
- [ ] Decide on priority order
- [ ] Start with highest priority type

### Short Term
- [ ] Document Time-Based Activities
- [ ] Document Funding Activities
- [ ] Create unified master index

### Long Term
- [ ] Document all remaining activity types
- [ ] Create search/filter functionality
- [ ] Add visual state diagrams (SVG)
- [ ] API integration for live data

---

**Last Updated:** October 30, 2025  
**Status:** Planning phase - 2/25 models documented (8%)

