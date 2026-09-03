# Email Message Preview System

This module includes a comprehensive email message preview system for all `TransitionMessage` classes across Bluebottle.

## Overview

The preview system automatically discovers and generates HTML previews of all email notifications in the platform, including:
- Activity notifications (approvals, rejections, updates)
- Participant notifications (applications, confirmations)
- Funding notifications (donations, campaigns)
- Grant management notifications
- Initiative notifications
- Team and slot notifications
- Member notifications

## Quick Start

### Generate All Previews (English & Dutch)

```bash
python manage.py preview_all_messages --all --all-languages
```

This generates previews in `bluebottle/notifications/static/email_previews/` which can be accessed via:
- **Static URL**: `/static/email_previews/index_all.html`
- **Direct file**: Open `bluebottle/notifications/static/email_previews/index_all.html` in a browser

### Generate Specific Module

```bash
python manage.py preview_all_messages --module activities
python manage.py preview_all_messages --module funding
```

### List Available Modules

```bash
python manage.py preview_all_messages --list-modules
```

## Features

### 🎨 Interactive Gallery
- **Modal Previews**: Click any email to open it in a full-screen modal
- **Language Switching**: Toggle between English and Dutch translations
- **Module Organization**: Messages grouped by their source module
- **Statistics Dashboard**: See counts of messages by category
- **Search/Filter**: Quickly find specific messages
- **Keyboard Navigation**: Press ESC to close modals

### 🌐 Multi-Language Support
- Generates previews for both English and Dutch
- Uses Django's translation system with `user.primary_language`
- Template content (email body) translates correctly via `{% blocktrans %}`
- Subject lines use `pgettext_lazy()` (Note: may not translate in standalone mode)

### 🤖 Smart Mocking System
The system automatically provides appropriate mock objects for different message types:
- `MockActivity`: For general activity messages
- `MockFunding`: For donation and funding messages
- `MockGrantApplication`: For grant-related messages
- `MockParticipant`: For participant/registration messages
- `MockTeam`: For team messages
- `MockSlot`: For time slot messages
- `MockInitiative`: For initiative messages
- `MockUpdate`: For update/wall post messages

## File Structure

```
bluebottle/notifications/
├── management/
│   └── commands/
│       └── preview_all_messages.py    # Main preview generation command
├── static/
│   └── email_previews/                # Generated preview files (gitignored)
│       ├── index_all.html             # Main gallery page
│       ├── metadata_all.json          # Message metadata
│       ├── activities.activity_manager/
│       ├── funding.messages/
│       └── ...                        # One folder per module
└── README_EMAIL_PREVIEWS.md           # This file
```

## How It Works

1. **Discovery**: Scans all registered message modules for `TransitionMessage` subclasses
2. **Mocking**: Creates appropriate mock objects (member, activity, funding, etc.)
3. **Rendering**: Uses Django's template system to render email HTML
4. **Translation**: Applies language context via `translation.override()`
5. **Saving**: Saves HTML files organized by module and language
6. **Gallery**: Generates interactive HTML gallery with modal support

## Viewing Previews

### Option 1: Via Django Static Files (Recommended)
1. Generate previews: `python manage.py preview_all_messages --all --all-languages`
2. Run server: `python manage.py runserver --settings=bluebottle.settings.local`
3. Visit: `http://[tenant].localhost:8000/static/assets/email_previews/index_all.html`
   - Example: `http://onepercent.localhost:8000/static/assets/email_previews/index_all.html`

### Option 2: Direct File Access
1. Generate previews
2. Open: `bluebottle/notifications/static/email_previews/index_all.html` in your browser

## Message Coverage

The system discovers messages from these modules:
- `activities.activity_manager` - Core activity lifecycle
- `activities.participant` - Participant notifications
- `activities.reviewer` - Review process
- `activities.matching` - Matching system
- `time_based.messages.participants` - Time-based participants
- `time_based.messages.teams` - Team management
- `time_based.messages.registrations` - Registration flows
- `time_based.messages.slots` - Time slots
- `funding.messages` - Donations & campaigns
- `grant_management.messages` - Grants
- `initiatives.messages` - Initiatives
- `deeds.messages` - Deed activities
- `collect.messages` - Collect activities
- `updates.messages` - Updates/wall posts
- `members.messages` - Member notifications

## Development

### Adding New Message Types
1. Create your `TransitionMessage` subclass as usual
2. No additional configuration needed - autodiscovery will find it
3. Regenerate previews to see it in the gallery

### Customizing Mock Data
Edit the mock classes in `preview_all_messages.py`:
- `MockMember` - User/member data
- `MockActivity` - Activity data
- `MockFunding` - Funding campaign data
- etc.

### Customizing Gallery Appearance
The gallery HTML/CSS is generated in the `generate_index()` function of `preview_all_messages.py`.

## Troubleshooting

### Database Errors
Some messages try to load platform settings from the database. These will be gracefully skipped with a warning.

### Missing Translations
- **Body content**: Should translate correctly via Django templates
- **Subject lines**: May not translate in preview mode due to `pgettext_lazy()` evaluation timing

### Preview Not Updating
Make sure to regenerate after code changes:
```bash
python manage.py preview_all_messages --all --all-languages
```

## Notes

- Preview files are gitignored (not committed to repo)
- Requires Django environment setup
- Uses mock data only - no database queries
- Safe to run in any environment

