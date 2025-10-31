# Email Message Preview System - Setup Complete ✅

## Overview

The email preview system is now fully integrated into the Bluebottle notifications module. All preview-related files have been moved to their proper locations within the Django project structure.

## File Organization

### Core Files
```
bluebottle/notifications/
├── management/
│   └── commands/
│       └── preview_all_messages.py    # Django management command
├── static/
│   └── email_previews/                # Generated preview files (gitignored)
│       ├── index_all.html             # Interactive gallery with modals
│       ├── metadata_all.json          # Message metadata for JS
│       └── [module_folders]/          # Organized by source module
│           ├── MessageName.html       # English preview
│           └── MessageName_nl.html    # Dutch preview
├── messages.py                        # TransitionMessage base class
├── README_EMAIL_PREVIEWS.md           # User documentation
└── PREVIEW_SYSTEM.md                  # This file
```

### Generated Files (Not in Git)
All files in `bluebottle/notifications/static/email_previews/` are gitignored as they are generated content.

## Quick Start

### Generate All Previews (Recommended)
```bash
# From project root
python manage.py preview_all_messages --all --all-languages
```

This generates:
- **146 email previews** (73 messages × 2 languages)
- **Interactive HTML gallery** with modal previews
- **Metadata JSON** for dynamic gallery features

### View Previews

#### Option 1: Via Django Static Files (Production)
```bash
python manage.py runserver --settings=bluebottle.settings.local
# Visit: http://[tenant].localhost:8000/static/assets/email_previews/index_all.html
# Example: http://onepercent.localhost:8000/static/assets/email_previews/index_all.html
```

#### Option 2: Direct File Access (Development)
```bash
xdg-open bluebottle/notifications/static/email_previews/index_all.html
# or
firefox bluebottle/notifications/static/email_previews/index_all.html
```

## Gallery Features

### 🎨 Interactive UI
- **Modal Previews**: Click any email card to open full preview in modal
- **Language Switcher**: Toggle between English (EN) and Dutch (NL)
- **Module Organization**: Messages grouped by source module
- **Statistics Dashboard**: See message counts by category
- **Keyboard Navigation**: ESC to close modals
- **Responsive Design**: Works on desktop and mobile

### 📊 Coverage Statistics
The system discovers and previews messages from 18 modules:
- Activity Management (10 messages)
- Funding & Donations (29 messages)
- Grant Management (9 messages)
- Time-based Activities (48 messages)
- Initiatives (16 messages)
- Participants & Teams (24 messages)
- Updates & Wall Posts (4 messages)
- Members (2 messages)
- And more...

**Total: 167 discovered messages, 146 successfully generated**

## Command Options

### List All Available Modules
```bash
python manage.py preview_all_messages --list-modules
```

### Generate Specific Module
```bash
python manage.py preview_all_messages --module activities
python manage.py preview_all_messages --module funding
python manage.py preview_all_messages --module time_based
```

### English Only (Faster)
```bash
python manage.py preview_all_messages --all
```

### Custom Output Directory
```bash
python manage.py preview_all_messages --all --output-dir /tmp/previews
```

## How It Works

### 1. Auto-Discovery
The system scans all registered message modules for `TransitionMessage` subclasses:
```python
MESSAGE_MODULES = {
    'activities.activity_manager': 'bluebottle.activities.messages.activity_manager',
    'funding.messages': 'bluebottle.funding.messages',
    'time_based.messages': 'bluebottle.time_based.messages',
    # ... 18 modules total
}
```

### 2. Smart Mocking
Automatically provides appropriate mock objects based on message type:
- `MockActivity` - General activity messages
- `MockFunding` - Donation/campaign messages
- `MockParticipant` - Participant notifications
- `MockTeam` - Team management
- `MockSlot` - Time slot scheduling
- `MockGrantApplication` - Grant applications
- `MockInitiative` - Initiative lifecycle
- `MockUpdate` - Wall posts/updates
- `MockMember` - User notifications

### 3. Multi-Language Rendering
- Uses Django's `translation.override(language)` context manager
- Generates both English and Dutch versions
- Respects `user.primary_language` setting
- Template content (`{% blocktrans %}`) translates correctly

### 4. Gallery Generation
- Creates interactive HTML with embedded CSS and JavaScript
- Generates `metadata_all.json` with message info and file paths
- Modal system for full-screen previews
- Language switching without page reload

## Known Limitations

### Some Messages Cannot Be Previewed
About 21 messages fail to generate due to:

1. **Database Dependencies**
   - Messages that load `InitiativePlatformSettings` or other DB models
   - Example: `TermsOfServiceNotification`

2. **Missing Mock Attributes**
   - Messages expecting specific object attributes not in mocks
   - Example: `DeedDateChangedNotification` expects `obj.start`

3. **Tenant Context Issues**
   - Messages using `connection.tenant.domain_url`
   - Example: `AccountActivationMessage`

4. **Template Issues**
   - Missing template files (e.g., `mails/messages/base.html`)
   - Example: `UpdateMessage`

These failures are **gracefully handled** and don't stop the generation of other previews.

### Subject Line Translations
- Subject lines use `pgettext_lazy()` which may not translate correctly in preview mode
- This is because lazy strings are evaluated at module import time
- Email **body content** translates correctly via Django templates
- See `TRANSLATION_NOTE.md` (in project root, if still exists) for details

## Adding New Messages

When you create a new `TransitionMessage` subclass:

1. **No configuration needed** - autodiscovery will find it
2. **Regenerate previews** to see it:
   ```bash
   python manage.py preview_all_messages --all --all-languages
   ```
3. **Check the gallery** - your message will appear in its module section

## Customization

### Adding Mock Attributes
Edit `preview_all_messages.py` to add attributes to mock classes:

```python
class MockActivity:
    def __init__(self, language='en'):
        self.title = "Clean up the local park"
        self.start = datetime.datetime.now()  # Add new attribute
        # ...
```

### Customizing Gallery Appearance
Edit the `generate_index()` function in `preview_all_messages.py` to:
- Change CSS styles
- Modify layout
- Add new features
- Customize modal behavior

### Adding New Mock Types
Add new mock classes for specialized message types:

```python
class MockNewFeature:
    def __init__(self, language='en'):
        # Define attributes needed by your messages
        pass

# Then update get_mock_object():
def get_mock_object(message_class, language='en'):
    if 'NewFeature' in message_class.__name__:
        return MockNewFeature(language)
    # ... existing logic
```

## Development Workflow

### Making Changes
1. Edit message classes or templates
2. Regenerate previews:
   ```bash
   python manage.py preview_all_messages --all --all-languages
   ```
3. Refresh browser to see changes

### Testing New Messages
```bash
# Test specific module
python manage.py preview_all_messages --module your_module

# Check for errors
# Failed messages will show error details in console
```

### CI/CD Integration
You can integrate preview generation into your CI pipeline:

```yaml
# Example: .gitlab-ci.yml
preview_emails:
  stage: test
  script:
    - python manage.py preview_all_messages --all
  artifacts:
    paths:
      - bluebottle/notifications/static/email_previews/
    expire_in: 7 days
```

## Troubleshooting

### Command Not Found
Make sure you're using the correct Python environment:
```bash
~/.virtualenvs/bluebottle/bin/python manage.py preview_all_messages --all
```

### Import Errors
Ensure Django is properly configured:
```bash
export DJANGO_SETTINGS_MODULE=bluebottle.settings.local
python manage.py preview_all_messages --all
```

### Preview Not Updating
1. Delete the output directory:
   ```bash
   rm -rf bluebottle/notifications/static/email_previews
   ```
2. Regenerate:
   ```bash
   python manage.py preview_all_messages --all --all-languages
   ```
3. Hard refresh browser (Ctrl+Shift+R)

### Modal Not Working
Check browser console for JavaScript errors. Ensure `metadata_all.json` exists and is valid JSON.

## Migration Notes

### Files Moved
Old locations → New locations:
- `preview_all_messages.py` → `bluebottle/notifications/management/commands/preview_all_messages.py`
- `all_message_previews/` → `bluebottle/notifications/static/email_previews/`
- `message_previews/` → (deleted, superseded by above)

### Old Documentation (Removed)
These files have been removed from the project root:
- `EMAIL_PREVIEW_README.md`
- `PREVIEW_SUMMARY.md`
- `MODAL_FEATURE_SUMMARY.md`
- `ALL_MESSAGES_SUMMARY.md`
- `QUICK_START.md`
- `COMPLETE_SYSTEM_SUMMARY.md`
- `preview_email_messages.py` (old activity-only script)

All documentation is now consolidated here and in `README_EMAIL_PREVIEWS.md`.

## Benefits

### For Developers
- **Visual verification** of email changes before deployment
- **Multi-language testing** without database setup
- **Quick iteration** on email templates
- **No database required** - pure mock-based rendering

### For Designers
- **See all emails** in one place
- **Compare versions** side-by-side (EN/NL)
- **Test responsive design** in different viewports
- **Preview with real HTML/CSS** rendering

### For QA
- **Systematic testing** of all email notifications
- **Visual regression testing** capability
- **Documentation** of all available messages
- **Easy sharing** - just open HTML file

## Future Enhancements

Potential improvements:
- [ ] Add search/filter functionality to gallery
- [ ] Generate comparison views (old vs new)
- [ ] Add screenshot generation for visual regression testing
- [ ] Export to PDF or static site
- [ ] Add more languages (French, German, etc.)
- [ ] Integration with email testing services (Litmus, Email on Acid)
- [ ] Automated preview generation on PR creation

## Support

For questions or issues:
1. Check `README_EMAIL_PREVIEWS.md` for detailed usage instructions
2. Review error messages in console output
3. Check Django settings and environment configuration
4. Verify all required packages are installed

---

**System Status**: ✅ Fully Operational
**Last Updated**: October 30, 2025
**Version**: 2.0 (Integrated into notifications module)

