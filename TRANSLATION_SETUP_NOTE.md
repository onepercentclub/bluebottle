# Translation Setup Issue

## Problem Found

Dutch translations are not appearing in email previews because:

1. **Translation files exist** in: `bluebottle/locale/nl/LC_MESSAGES/django.po/mo`
2. **But Django is configured** to look in: `/home/gannetson/Projects/server-deployment/translations/base`
3. **That directory doesn't exist** on this system

## Current Configuration

In `bluebottle/settings/local.py`:
```python
GOODUP_TRANSLATIONS_PATH = os.path.join(...)
LOCALE_PATHS = [os.path.join(GOODUP_TRANSLATIONS_PATH, "base")]
```

This overrides the base setting which points to the correct location:
```python
# In bluebottle/settings/base.py
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale/'), )
```

## Solutions

### Option 1: Use Base Settings (Recommended for Local Development)
Comment out the `LOCALE_PATHS` override in `local.py`:
```python
# LOCALE_PATHS = [os.path.join(GOODUP_TRANSLATIONS_PATH, "base")]
```

### Option 2: Fix the Path in local.py
Update `local.py` to point to the correct location:
```python
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]
```

### Option 3: Create Symlink
```bash
mkdir -p /home/gannetson/Projects/server-deployment/translations
ln -s /home/gannetson/Projects/bluebottle/locale /home/gannetson/Projects/server-deployment/translations/base
```

## For Email Previews

The preview command now includes enhanced language forcing in `messages.py`:
- `django_translation.activate(recipient.primary_language)` in `get_messages()`
- `django_translation.activate(recipient.primary_language)` in `get_content_html()`

Once the LOCALE_PATHS issue is fixed, Dutch translations should work for:
- ✅ Email body content (`{% blocktrans %}` tags)
- ⚠️  Subject lines (`pgettext_lazy`) - may still show English due to lazy evaluation timing

## Testing

After fixing LOCALE_PATHS, test with:
```bash
python manage.py preview_all_messages --module activities.activity_manager --all-languages
```

Check if the Dutch HTML files show translated content.
