# How to Generate Documentation for Collect (or any FSM model)

You have **three options** to generate documentation for Collect or any other FSM model:

---

## Option 1: Use the Existing Markdown Documentation ✅ EASIEST

**The Collect models are already fully documented!**

Open **[FSM_COMPLETE_DOCUMENTATION.md](FSM_COMPLETE_DOCUMENTATION.md)** and go to:
- **Section 15:** CollectActivity
- **Section 16:** CollectContributor

This includes:
- ✅ All states with descriptions
- ✅ All transitions with conditions/permissions
- ✅ All triggers and effects
- ✅ All notifications

**No generation needed - just use the existing documentation!**

---

## Option 2: Copy and Adapt the Deed Generator (Recommended for HTML)

The Deed HTML generator uses a **dictionary-based approach** that's easy to customize:

### Steps:

1. **Copy the deed generator:**
   ```bash
   cp generate_deed_state_pages.py generate_collect_state_pages_dict.py
   ```

2. **Edit the dictionaries at the top:**
   - Replace `DEED_STATES` with `COLLECT_ACTIVITY_STATES`
   - Replace `DEED_PARTICIPANT_STATES` with `COLLECT_CONTRIBUTOR_STATES`
   - Update state names, descriptions, transitions

3. **Update the data from FSM_COMPLETE_DOCUMENTATION.md:**
   - Copy state information from Section 15 & 16
   - Format as Python dictionaries
   - Include all transitions, effects, notifications

4. **Run the generator:**
   ```bash
   source ~/.virtualenvs/bluebottle/bin/activate
   python generate_collect_state_pages_dict.py
   ```

### Example Dictionary Structure:

```python
COLLECT_ACTIVITY_STATES = {
    'draft': {
        'name': 'Draft',
        'value': 'draft',
        'description': 'Activity created, not yet completed.',
        'outgoing': [
            {
                'name': 'submit',
                'to': 'submitted',
                'type': 'manual',
                'description': 'Submit for review',
                'permission': ['is_owner'],
                'conditions': ['is_complete()', 'is_valid()']
            },
            # ... more transitions
        ],
        'incoming': [
            {'name': 'initiate', 'from': 'EmptyState'}
        ]
    },
    # ... more states
}
```

---

## Option 3: Quick Manual HTML Creation

For a quick HTML visualization without a generator:

### 1. Create directory:
```bash
mkdir collect_states_visualization
```

### 2. Copy the CSS:
```bash
cp deed_states_visualization/state_styles.css collect_states_visualization/
```

### 3. Create a simple index.html:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Collect States</title>
    <link rel="stylesheet" href="state_styles.css">
</head>
<body>
    <div class="container">
        <h1>Collect States Documentation</h1>
        <p>See FSM_COMPLETE_DOCUMENTATION.md for complete details</p>
        
        <h2>CollectActivity States</h2>
        <ul>
            <li>draft → submitted → open → succeeded</li>
            <li>Can also: cancel, expire, reject</li>
        </ul>
        
        <h2>CollectContributor States</h2>
        <ul>
            <li>new → accepted → succeeded</li>
            <li>Can also: withdraw, remove (reject)</li>
        </ul>
        
        <p><a href="../FSM_COMPLETE_DOCUMENTATION.md">View complete documentation →</a></p>
    </div>
</body>
</html>
```

---

## Recommended Approach

**For most use cases:** Just use the **FSM_COMPLETE_DOCUMENTATION.md** file. It has everything you need:

### Quick Access:

```bash
# View in terminal
less FSM_COMPLETE_DOCUMENTATION.md

# Or open in your editor
code FSM_COMPLETE_DOCUMENTATION.md

# Jump to Collect section
# Search for: "## 15. CollectActivity"
```

### What's Already There:

**CollectActivity** includes:
- 8 states (draft, submitted, needs_work, open, succeeded, cancelled, rejected, expired)
- 13 transitions (submit, approve, publish, succeed, expire, cancel, etc.)
- ModelChangedTriggers (start, end)
- TransitionTriggers with full effects
- 5+ notifications mapped

**CollectContributor** includes:
- 6 states (new, accepted, succeeded, failed, withdrawn, rejected)
- 9 transitions (initiate, succeed, withdraw, reapply, remove, etc.)
- Complete trigger and effect mapping
- Multiple notification types

---

## For Other Models

The same approach works for **any FSM model**:

1. **Check FSM_COMPLETE_DOCUMENTATION.md first** - it likely already has what you need
2. **For HTML visualization**, copy the deed generator pattern
3. **For quick reference**, the markdown is comprehensive and searchable

---

## All Available Documentation

| Model | Markdown Docs | HTML Viz |
|-------|--------------|----------|
| **Deeds** | ✅ FSM_COMPLETE_DOCUMENTATION.md + DEED_LIFECYCLE.md | ✅ deed_states_visualization/ |
| **CollectActivity** | ✅ FSM_COMPLETE_DOCUMENTATION.md #15 | ⚪ (Can generate) |
| **CollectContributor** | ✅ FSM_COMPLETE_DOCUMENTATION.md #16 | ⚪ (Can generate) |
| **DateActivity** | ✅ FSM_COMPLETE_DOCUMENTATION.md #1 | ⚪ (Can generate) |
| **Funding** | ✅ FSM_COMPLETE_DOCUMENTATION.md #12 | ⚪ (Can generate) |
| **All 18 models** | ✅ FSM_COMPLETE_DOCUMENTATION.md | ⚪ Deed only |

---

## Need Help?

- **Understanding Collect flows?** → See FSM_COMPLETE_DOCUMENTATION.md sections 15-16
- **Want interactive HTML?** → Copy deed generator and adapt dictionaries
- **Quick reference?** → FSM_QUICK_START.md has examples
- **Questions about specific transitions?** → Search in FSM_COMPLETE_DOCUMENTATION.md

---

## Summary

**You already have complete Collect documentation in FSM_COMPLETE_DOCUMENTATION.md!**

To generate HTML like the Deed visualization:
1. Copy `generate_deed_state_pages.py`
2. Update the dictionary data at the top
3. Run the script

But for most purposes, the markdown documentation is comprehensive and sufficient. 🎉

