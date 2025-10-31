# FSM Documentation - Quick Start Guide

**Get started with Bluebottle FSM documentation in 5 minutes**

---

## 🚀 Quick Navigation

### I want to understand a specific model

**→ Go to: [FSM_COMPLETE_DOCUMENTATION.md](FSM_COMPLETE_DOCUMENTATION.md)**

Use the table of contents to jump to your model:
- Time-Based Activities (#1-5)
- Time-Based Participants (#6-11)
- Funding (#12-14)
- Collect Activities (#15-16)
- Deeds (#17-18)

Each model includes:
- ✅ All states with descriptions
- ✅ All transitions (manual/automatic)
- ✅ Conditions and permissions
- ✅ Triggers and effects
- ✅ Notifications

---

### I want to see it visually/interactively

**→ Open in browser: [deed_states_visualization/index.html](deed_states_visualization/index.html)**

Interactive features:
- 🖱️ Click on states to explore
- 🔗 Follow transition links to next state
- 👁️ See all effects and notifications
- 📱 Works on mobile too

---

### I want a high-level overview

**→ Read: [FSM_DOCUMENTATION_SUMMARY.md](FSM_DOCUMENTATION_SUMMARY.md)**

Includes:
- 📊 Coverage statistics
- 🎯 Key features
- 💡 Usage guides for developers/PMs/QA
- 🔍 Pattern analysis

---

### I'm debugging a state issue

**Step 1:** Find your model in [FSM_COMPLETE_DOCUMENTATION.md](FSM_COMPLETE_DOCUMENTATION.md)

**Step 2:** Check:
- Current state of your object
- Valid transitions from that state
- Required conditions
- Required permissions

**Step 3:** Verify conditions are met:
```python
# Example for Deed
deed.status  # Check current state
deed.is_complete()  # Check if complete
deed.is_valid()  # Check if valid
# Check user permissions
```

---

### I'm adding a new feature

**Step 1:** Understand current flow
- Read model documentation
- Review all related states
- Check existing transitions

**Step 2:** Identify integration points
- Where does new transition fit?
- What triggers should fire?
- What effects are needed?
- What notifications to send?

**Step 3:** Update documentation
- Add new states/transitions
- Document conditions/permissions
- Update triggers/effects
- Regenerate if needed

---

## 📁 All Documentation Files

| File | Purpose | Lines |
|------|---------|-------|
| **FSM_COMPLETE_DOCUMENTATION.md** | Complete reference for all 18 models | 10,000+ |
| **FSM_DOCUMENTATION_SUMMARY.md** | Project overview and statistics | 400+ |
| **STATE_MACHINES_OVERVIEW.md** | Architecture analysis | 400+ |
| **DEED_LIFECYCLE.md** | Detailed Deed documentation | 600+ |
| **DEED_INHERITED_TRIGGERS_ADDENDUM.md** | Inherited behavior | 300+ |
| **deed_states_visualization/** | Interactive HTML (16 pages) | - |
| **Generator scripts** | Regenerate documentation | 4 files |

---

## 🔍 Common Queries

### "What are all the states for Funding?"

→ [FSM_COMPLETE_DOCUMENTATION.md#12-funding](FSM_COMPLETE_DOCUMENTATION.md#12-funding)

States: draft, submitted, needs_work, open, succeeded, partially_funded, refunded, cancelled, rejected, on_hold

### "How does a participant get accepted?"

→ [FSM_COMPLETE_DOCUMENTATION.md#6-11-time-based-participants](FSM_COMPLETE_DOCUMENTATION.md#6-11-time-based-participants)

Via `accept` transition: new/withdrawn/removed/rejected → accepted

### "What notifications are sent when an activity succeeds?"

→ Look up model in FSM_COMPLETE_DOCUMENTATION.md, find `succeed` transition, check effects section for `NotificationEffect`

### "Can a cancelled activity be restored?"

→ Yes! Check the `restore` transition in the model documentation

### "What conditions must be met to submit an activity?"

→ Find your activity model, look at `submit` transition conditions (usually: `is_complete`, `is_valid`, `can_submit`)

---

## 💡 Pro Tips

### For Developers
1. **Bookmark** FSM_COMPLETE_DOCUMENTATION.md
2. **Search** in documentation (Ctrl+F / Cmd+F)
3. **Cross-reference** with source code
4. **Update** docs when adding features

### For QA
1. **Test all transitions** for your feature
2. **Verify conditions** (both true and false)
3. **Check notifications** are sent correctly
4. **Test permissions** for manual transitions

### For Product Managers
1. **Review state descriptions** to understand user experience
2. **Follow transition flows** to see complete journey
3. **Check conditions** to identify user blockers
4. **Review notifications** for communication touchpoints

---

## 🔄 Keeping Documentation Current

### When code changes:

1. **Update markdown:**
   - Edit FSM_COMPLETE_DOCUMENTATION.md
   - Add new states/transitions
   - Document new effects

2. **Regenerate HTML (for Deeds):**
   ```bash
   source ~/.virtualenvs/bluebottle/bin/activate
   python generate_deed_state_pages.py
   ```

3. **Verify changes:**
   - Check documentation matches code
   - Test transitions
   - Verify notifications

---

## 📞 Need Help?

- **Understanding a model?** → Start with FSM_COMPLETE_DOCUMENTATION.md
- **Need visual representation?** → Open deed_states_visualization/index.html
- **Want overview?** → Read FSM_DOCUMENTATION_SUMMARY.md
- **Debugging?** → Check conditions and permissions in docs
- **Adding features?** → Review existing patterns first

---

## ✨ Key Concepts

### States
Current condition of an object (e.g., 'draft', 'open', 'succeeded')

### Transitions
Movement from one state to another (can be manual or automatic)

### Triggers
Events that fire when transitions occur or fields change

### Effects
Actions performed when triggers fire (transitions, notifications, etc.)

### Conditions
Requirements that must be met for a transition to occur

### Permissions
User permission checks for manual transitions

---

**You're all set!** Start with [FSM_COMPLETE_DOCUMENTATION.md](FSM_COMPLETE_DOCUMENTATION.md) and explore from there.

Happy coding! 🚀

