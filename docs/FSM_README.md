# Bluebottle FSM Documentation

**Complete documentation for all Finite State Machine models in the Bluebottle platform**

---

## 🚀 Quick Start

### 1. **Open the Master Portal** (Recommended!)

```bash
# Open in browser:
open fsm_documentation_portal.html
```

**Features:**
- 🔍 Search all 18 models
- 📊 Visual model cards with complexity indicators
- 🔗 Direct links to documentation
- 📱 Mobile-friendly interface

### 2. **View Complete Documentation**

```bash
# Open the comprehensive guide:
open FSM_COMPLETE_DOCUMENTATION.md
```

**Includes:**
- All 18 models fully documented
- States, transitions, triggers, effects
- Notifications with subjects and recipients
- Complete inheritance chains

### 3. **Try Interactive Example**

```bash
# Open Deed interactive visualization:
open deed_states_visualization/index.html
```

**Features:**
- Clickable state transitions
- Visual effects and notifications
- Professional design

---

## 📚 Documentation Files

### Main Documentation

| File | Description | Size |
|------|-------------|------|
| **fsm_documentation_portal.html** | Master portal with search | NEW! |
| **FSM_COMPLETE_DOCUMENTATION.md** | All 18 models documented | 33KB |
| **FSM_QUICK_START.md** | 5-minute guide | 9KB |
| **FSM_DOCUMENTATION_SUMMARY.md** | Project overview | 13KB |
| **DEED_LIFECYCLE.md** | Detailed Deed docs | 22KB |
| **STATE_MACHINES_OVERVIEW.md** | Architecture analysis | 21KB |

### Interactive Visualizations

| Directory | Models | Pages |
|-----------|--------|-------|
| **deed_states_visualization/** | Deed, DeedParticipant | 16 HTML pages |

### Generators

| Script | Purpose |
|--------|---------|
| **generate_master_fsm_portal.py** | Master portal |
| **generate_deed_state_pages.py** | Deed HTML generator |
| **generate_participant_state_pages.py** | Participant HTML |
| **generate_universal_fsm_docs.py** | Universal generator |

---

## 📊 Coverage

### ✅ 100% Complete (18/18 Models)

**Time-Based Activities** (5 models)
- DateActivity, DeadlineActivity, ScheduleActivity, PeriodicActivity, RegisteredDateActivity

**Time-Based Participants** (6 models)
- DateParticipant, DeadlineParticipant, ScheduleParticipant, TeamScheduleParticipant, PeriodicParticipant, RegisteredDateParticipant

**Funding** (3 models)
- Funding, Donor, Payment

**Collect Activities** (2 models)
- CollectActivity, CollectContributor

**Deeds** (2 models)
- Deed, DeedParticipant

### Documentation Statistics

- **72+** State Machine Classes
- **69+** Distinct States
- **137+** Transitions
- **168+** Triggers
- **107+** Notifications
- **~60,000** Lines of documentation

---

## 🎯 Usage Guide

### For Developers

**Understanding a model:**
```bash
1. Open fsm_documentation_portal.html
2. Search for your model
3. Click "View Documentation"
4. Review states, transitions, triggers
```

**Debugging state issues:**
```bash
1. Find model in FSM_COMPLETE_DOCUMENTATION.md
2. Check current state
3. Verify transition conditions
4. Check required permissions
```

### For Product Managers

**Understanding user flows:**
```bash
1. Open fsm_documentation_portal.html
2. Find relevant model
3. Review state descriptions
4. Follow transition paths
5. Check notification triggers
```

### For QA/Testing

**Test coverage:**
```bash
1. Review all transitions for model
2. Test all conditions (true/false)
3. Verify notifications sent
4. Test permission checks
```

---

## 🔍 Finding Information

### By Model Name

1. Open `fsm_documentation_portal.html`
2. Use search box (e.g., "funding", "deadline")
3. Click model card
4. View documentation

### By Feature

1. Open `FSM_COMPLETE_DOCUMENTATION.md`
2. Use Ctrl+F / Cmd+F
3. Search for: state name, transition, notification

### By Category

1. Open `fsm_documentation_portal.html`
2. Scroll to category section
3. Browse models in category

---

## 🛠️ Generating HTML for Other Models

To create interactive HTML visualization (like Deeds) for any model:

```bash
# Step 1: Copy the template
cp generate_deed_state_pages.py generate_YOUR_MODEL_pages.py

# Step 2: Edit dictionaries (lines 10-800)
# - Replace DEED_STATES with YOUR_MODEL_STATES
# - Copy data from FSM_COMPLETE_DOCUMENTATION.md
# - Format as Python dictionaries

# Step 3: Run generator
source ~/.virtualenvs/bluebottle/bin/activate
python generate_YOUR_MODEL_pages.py

# Output: your_model_visualization/ directory
```

See `GENERATE_COLLECT_DOCS.md` for detailed instructions.

---

## 📖 Documentation Formats

### 1. Master Portal (HTML)
- **File:** `fsm_documentation_portal.html`
- **Best for:** Overview, browsing, discovery
- **Features:** Search, visual cards, quick links

### 2. Complete Guide (Markdown)
- **File:** `FSM_COMPLETE_DOCUMENTATION.md`
- **Best for:** Reference, detailed lookup
- **Features:** Complete, searchable, printable

### 3. Interactive Visualizations (HTML)
- **Directory:** `deed_states_visualization/`
- **Best for:** Learning, presentations
- **Features:** Clickable, visual, engaging

### 4. Quick Reference (Markdown)
- **File:** `FSM_QUICK_START.md`
- **Best for:** Getting started, common queries
- **Features:** Examples, shortcuts, FAQ

---

## 🔄 Keeping Documentation Current

### When code changes:

1. **Update markdown:**
   ```bash
   # Edit FSM_COMPLETE_DOCUMENTATION.md
   # Update relevant sections
   ```

2. **Regenerate portal:**
   ```bash
   python generate_master_fsm_portal.py
   ```

3. **Regenerate HTML (if needed):**
   ```bash
   source ~/.virtualenvs/bluebottle/bin/activate
   python generate_deed_state_pages.py
   ```

### Periodic reviews:

- Compare docs to source code
- Update statistics
- Add new models/states
- Refresh examples

---

## 📁 Project Structure

```
bluebottle/
├── fsm_documentation_portal.html    # ⭐ Master portal (START HERE)
│
├── FSM_COMPLETE_DOCUMENTATION.md    # Complete reference
├── FSM_QUICK_START.md               # Quick guide
├── FSM_DOCUMENTATION_SUMMARY.md     # Project overview
├── FSM_README.md                    # This file
│
├── DEED_LIFECYCLE.md                # Detailed Deed docs
├── DEED_INHERITED_TRIGGERS_ADDENDUM.md
├── STATE_MACHINES_OVERVIEW.md       # Architecture
├── GENERATE_COLLECT_DOCS.md         # How-to guide
│
├── deed_states_visualization/       # Interactive HTML
│   ├── index.html
│   ├── state_styles.css
│   └── [14 state pages]
│
└── generators/
    ├── generate_master_fsm_portal.py
    ├── generate_deed_state_pages.py
    ├── generate_participant_state_pages.py
    └── generate_universal_fsm_docs.py
```

---

## 🎨 Features

### Master Portal
✅ Search functionality  
✅ Visual model cards  
✅ Complexity indicators  
✅ Category organization  
✅ Direct documentation links  
✅ Mobile-responsive  

### Complete Documentation
✅ All 18 models  
✅ States & descriptions  
✅ Transitions & conditions  
✅ Triggers & effects  
✅ Notifications  
✅ Inheritance chains  

### Interactive Visualizations
✅ Clickable transitions  
✅ Visual effects  
✅ Professional design  
✅ Mobile-friendly  

---

## 🚨 Important Notes

1. **Markdown is authoritative:** `FSM_COMPLETE_DOCUMENTATION.md` is the single source of truth
2. **HTML is generated:** Portal and visualizations are generated from markdown
3. **Always update markdown first:** Then regenerate HTML if needed
4. **Portal is entry point:** Use `fsm_documentation_portal.html` for navigation

---

## 💡 Tips

### For Quick Lookups
```bash
# Search in complete docs
grep -i "collectactivity" FSM_COMPLETE_DOCUMENTATION.md

# Or use portal search
open fsm_documentation_portal.html
```

### For Deep Dives
```bash
# Read specific section
less FSM_COMPLETE_DOCUMENTATION.md
# Then search: /CollectActivity
```

### For Presentations
```bash
# Use interactive HTML
open deed_states_visualization/index.html
```

---

## 🎯 Success Metrics

- ✅ **100% model coverage** (18/18)
- ✅ **Complete documentation** (states, transitions, triggers, effects)
- ✅ **Multiple formats** (HTML portal, markdown, interactive)
- ✅ **Searchable** (portal search + text search)
- ✅ **Maintainable** (generators for updates)
- ✅ **Professional** (polished design, good UX)

---

## 🙏 Credits

Documentation generated through systematic analysis of:
- State machine definitions (`bluebottle/*/states.py`)
- Trigger definitions (`bluebottle/*/triggers.py`)
- Message definitions (`bluebottle/*/messages/`)
- FSM framework (`bluebottle/fsm/`)

---

## 📞 Support

**Questions about documentation?**
- Check `FSM_QUICK_START.md` for common queries
- Search `FSM_COMPLETE_DOCUMENTATION.md`
- Browse `fsm_documentation_portal.html`

**Need to generate HTML for a model?**
- See `GENERATE_COLLECT_DOCS.md` for step-by-step guide
- Copy `generate_deed_state_pages.py` as template

**Want to update documentation?**
- Edit `FSM_COMPLETE_DOCUMENTATION.md`
- Run `python generate_master_fsm_portal.py`
- Regenerate HTML if needed

---

**🎉 You're all set! Start with `fsm_documentation_portal.html`**

