# Email Preview System - Language Configuration ✅

## Configuration

### Overview Buttons (Gallery)
Only **EN** and **NL** buttons are shown in the main gallery for quick access:
- 🇬🇧 EN
- 🇳🇱 NL

### Modal Language Switcher
The modal shows **ALL available languages** for that message:
- 🇩🇪 German (de)
- 🇬🇧 English (en)
- 🇪🇸 Spanish (es)
- 🇫🇷 French (fr)
- 🇭🇺 Hungarian (hu)
- 🇳🇱 Dutch (nl)
- 🇵🇹 Portuguese (pt)

**Note**: Bulgarian (bg) has been removed from the system.

## Usage

### Generate with Multiple Languages
```bash
# All 7 languages
python manage.py preview_all_messages --all --all-languages

# Specific languages (e.g., EN, NL, FR, DE)
python manage.py preview_all_messages --all --languages "en,nl,fr,de"

# Just EN and NL for quick iteration
python manage.py preview_all_messages --all --languages "en,nl"
```

### Available Languages
The system supports 7 languages (BG removed):
- `de` - German
- `en` - English
- `es` - Spanish
- `fr` - French
- `hu` - Hungarian
- `nl` - Dutch
- `pt` - Portuguese

## How It Works

### 1. Gallery View
- Shows only 🇬🇧 EN and 🇳🇱 NL buttons
- Keeps the interface clean
- Quick access to most commonly used languages

### 2. Modal View
- Opens with the selected language
- Shows **all generated languages** in the language switcher
- Only displays buttons for languages that were actually generated
- Example: If you generated EN, NL, FR, DE, the modal will show 4 buttons

### 3. Language Switching
- Click any language button in the modal
- Preview instantly switches to that language
- Button state updates to show active language
- Works seamlessly

## Examples

### Example 1: Generate EN and NL only
```bash
python manage.py preview_all_messages --all --languages "en,nl"
```
- **Overview**: Shows 🇬🇧 EN and 🇳🇱 NL buttons
- **Modal**: Shows 🇬🇧 EN and 🇳🇱 NL buttons

### Example 2: Generate all languages
```bash
python manage.py preview_all_messages --all --all-languages
```
- **Overview**: Shows only 🇬🇧 EN and 🇳🇱 NL buttons
- **Modal**: Shows all 7 language buttons (DE, EN, ES, FR, HU, NL, PT)

### Example 3: Generate EN, NL, FR, DE
```bash
python manage.py preview_all_messages --all --languages "en,nl,fr,de"
```
- **Overview**: Shows 🇬🇧 EN and 🇳🇱 NL buttons
- **Modal**: Shows 🇬🇧 EN, 🇳🇱 NL, 🇫🇷 FR, 🇩🇪 DE buttons

## Translations Verified Working

**ActivityApprovedNotification** example:
- 🇬🇧 EN: "Your activity on Example Tenant has been approved!"
- 🇳🇱 NL: "Je activiteit op Example Tenant is goedgekeurd!"
- 🇫🇷 FR: "Votre activité sur Example Tenant a été approuvée !"
- 🇩🇪 DE: "Ihre Aktivität auf Example Tenant wurde genehmigt!"
- 🇪🇸 ES: "¡Tu actividad en Example Tenant ha sido aprobada!"

## Technical Details

### File Naming
All preview files include language suffix:
```
MessageName_en.html
MessageName_nl.html
MessageName_fr.html
MessageName_de.html
etc.
```

### Metadata Structure
```json
{
  "languages": ["de", "en", "es", "fr", "hu", "nl", "pt"],
  "modules": {
    "activities.activity_manager": {
      "messages": [
        {
          "name": "ActivityApprovedNotification",
          "previews": {
            "en": "activities_activity_manager/ActivityApprovedNotification_en.html",
            "nl": "activities_activity_manager/ActivityApprovedNotification_nl.html",
            "fr": "activities_activity_manager/ActivityApprovedNotification_fr.html",
            "de": "activities_activity_manager/ActivityApprovedNotification_de.html"
          }
        }
      ]
    }
  }
}
```

### Code Changes

**1. Removed Bulgarian (bg)**
```python
available_languages = ['de', 'en', 'es', 'fr', 'hu', 'nl', 'pt']
```

**2. Overview shows only EN/NL**
```python
overview_languages = [lang for lang in ['en', 'nl'] if lang in languages]
for lang in overview_languages:
    html += f'<button class="lang-btn" onclick="openModal(...)">{flag} {lang.upper()}</button>'
```

**3. Modal shows all generated languages**
```javascript
langSelector.innerHTML = metadata.languages
    .filter(lang => messageData.previews[lang])
    .map(lang => `<button>${flag} ${lang.toUpperCase()}</button>`)
    .join('');
```

## View the Gallery

```bash
# Via Django server
python manage.py runserver --settings=bluebottle.settings.local
# Visit: http://onepercent.localhost:8000/static/assets/email_previews/index_all.html

# Or open directly
xdg-open bluebottle/notifications/static/email_previews/index_all.html
```

---

**Status**: ✅ Complete
**Overview Languages**: EN, NL only
**Modal Languages**: All generated languages
**Removed**: Bulgarian (bg)
