# Platform color contrast accessibility — design

**Date:** 2026-07-23  
**Status:** Approved — implemented (v1)  
**Primary repo:** bluebottle (Django admin / platform settings)  
**Consuming app:** marlin (no changes in v1)

## Problem

Platform operators choose brand colors in Bluebottle Django admin (`SitePlatformSettings` Styling fieldset). Those colors are exposed via `GET /api/config` and applied in Marlin as Chakra theme tokens (action, description, link, footer).

Today:

- Help text only warns that light action/description colors may need darker text.
- There is **no** contrast calculation or UI feedback for platform colors on save or while editing.
- Segments already auto-derive label text polarity with `wcag-contrast-ratio` — platform styling does not reuse that pattern.
- Marlin defaults missing text colors to white, so a light `action_color` with white `action_text_color` ships inaccessible buttons.

Clients can brand the platform in ways that fail WCAG contrast for buttons, links, and footer text.

## Goals (v1)

1. Give admins **live** WCAG 2.2 AA feedback while editing platform colors.
2. Show a **mini preview** (button, link, footer) so failures are obvious without leaving admin.
3. On save, if any checked pair fails AA, show a **soft warning** (Django `message_user`). **Never block save.**
4. Reuse existing Bluebottle contrast tooling where practical (`wcag-contrast-ratio`, already a dependency).

## Non-goals (v1)

- Hard validation / refusing to save failing colors
- Auto-fixing or auto-deriving text colors (segments-style) for platform settings
- Marlin-side validation or UI
- Checking derived Marlin palette stops (`action.100` … `action.900`)
- APCA / WCAG 3 as the compliance gate
- Email-template-specific contrast beyond the same shared pairs
- Color-blindness simulation

## Decisions

| Topic | Choice |
| --- | --- |
| Enforcement | Soft warning only (can always save) |
| Standard | WCAG 2.2 AA (see Industry) |
| Pairs | Explicit stored pairs + link on page background |
| UX | Live ratios/badges + button / link / footer preview |
| Architecture | Admin JS for live UX + small Python helper for save-time message |
| Scope | Bluebottle admin only |

## Industry context — how others solve this

### Compliance floor: WCAG 2.x AA

Regulators, VPATs, and procurement still audit against **WCAG 2.1/2.2** contrast ratios, not APCA. Typical thresholds:

| Use | AA minimum |
| --- | --- |
| Normal text / button label text | **4.5:1** |
| Large text (≥18pt / ≥14pt bold) | **3:1** |
| Non-text UI (borders, icons) | **3:1** ([1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)) |

APCA is a useful design heuristic for readability (especially dark UI), but as of 2026 it is **not** the WCAG 3 normative algorithm and was pulled from WCAG 3 working drafts as exploratory. Shipping “APCA-only” pairs that fail WCAG 2 is not a defensible compliance posture. See [Adrian Roselli — WCAG3 Contrast as of April 2026](https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html) and [Z.Tools — WCAG 2 vs APCA](https://z.tools/blog/apca-vs-wcag-contrast).

**v1 uses WCAG 2.2 relative luminance + AA pass/fail.** APCA can be a later optional second score, never a replacement for AA messaging.

### Patterns in SaaS / theme customization

| Pattern | Who / where | Fit for us |
| --- | --- | --- |
| Educate + external checker | [Shopify theme accessibility](https://help.shopify.com/en/manual/online-store/themes/customizing-themes/accessibility) — docs + third-party tools; no native blocker | Too weak alone; we already have help text and still get bad pairs |
| Soft guidance at edit time | Contrast checkers / theme generators that show ratio + pass/fail while picking colors ([ChromUI](https://chromui.app/accessibility), palette builders) | **Matches v1** |
| Semantic pair matrices | Validate role pairs (button text, body text, links, borders), not one hex in isolation ([Color Safe Palette Builder](https://66colorful.com/tools/color-safe-palette-builder)) | **Matches v1** pair list |
| Generate tokens from brand | Tools that build full light/dark token sets with WCAG checks before export ([rgba→theme generators](https://rgbatohex.com/tools/light-dark-theme-generator)) | Future; we already store explicit text colors |
| Auto-derive foreground | Our own segments `text_color` property | Deferred — conflicts with soft warning + manual text fields |

**Takeaway:** Best practice for white-label brand settings is **validate the semantic pairs that actually appear in the product**, give **immediate visual feedback**, and keep **brand freedom** (warn, don’t hard-block) unless legal/compliance policy requires blocking.

## Current system (as-is)

### Bluebottle

`cms.SitePlatformSettings` color fields (django-colorfield):

- `action_color` / `action_text_color`
- `alternative_link_color` (optional)
- `description_color` / `description_text_color`
- `footer_color` / `footer_text_color`
- `link_color` property → `alternative_link_color or action_color`

Admin: `SitePlatformSettingsAdmin` Styling fieldset. Serialized into platform config for the frontend.

Segments precedent (`segments.Segment.text_color`):

```python
contrast.rgb(rgb_background, white)
contrast.passes_AA(..., large=True)  # choose white vs "text"
```

### Marlin

`getTheme(content)` maps config colors into Chakra tokens; `colorToPalette` expands action/description/link into 100–900 scales. Buttons use `action.500` + `actionText`; links use `link.500` on light pages; footer uses `footer` / `footerText`. No config-time contrast gate.

## Target architecture (v1)

```text
┌─────────────────────────────────────────────────────────┐
│  Django admin — SitePlatformSettings (Styling)          │
│                                                         │
│  ColorField inputs (django-colorfield)                  │
│           │                                             │
│           ▼                                             │
│  Admin JS: contrast math + badges + preview strip       │
│           │                                             │
│           ▼                                             │
│  Save ──► Python helper (wcag-contrast-ratio)           │
│           │                                             │
│           └─► message_user(WARNING) if any AA fail      │
│               (save always succeeds)                    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
              GET /api/config (unchanged)
                         │
                         ▼
              Marlin theme (unchanged in v1)
```

### Layer A — Live admin UI

Custom admin static JS/CSS attached to `SitePlatformSettingsAdmin`.

**Behavior:**

- Listen to color input `change` / `input` events.
- For each pair, compute WCAG contrast ratio (relative luminance) in JS.
- Show ratio (e.g. `4.2:1`) and **Pass AA** / **Fail AA**.
- On fail, short hint: text may be hard to read on this background.
- **Preview strip** (updates live):
  - Primary button: `action_color` background + `action_text_color` label
  - Link: `link_color` on `#FFFFFF`
  - Footer bar: `footer_color` + `footer_text_color`
  - Description chip: `description_color` + `description_text_color` (same pattern as button)

**Placement:** Contrast panel / strip under the Styling color fields on the change form.

**JS math:** Mirror WCAG 2 relative luminance client-side (small self-contained helper or vendored snippet). Live UI must not depend on a network round-trip.

### Layer B — Soft save summary

Python module, e.g. `bluebottle/cms/utils/color_contrast.py`:

- `contrast_ratio(fg, bg) -> float`
- `passes_aa(fg, bg, *, large=False) -> bool` — for v1 button/link/footer text use **normal text** AA (`passes_AA(..., large=False)` → 4.5:1)
- `evaluate_platform_colors(settings) -> list[PairResult]`

`PairResult` fields: `id`, `label`, `foreground`, `background`, `ratio`, `passes`.

Wire in `SitePlatformSettingsAdmin.save_model`: if any `passes` is false, `self.message_user(..., level=messages.WARNING)` listing failing pairs and ratios. Do **not** raise `ValidationError`.

If all pass: no extra message (avoid noise).

## Pairs and thresholds (v1)

| ID | Foreground | Background | AA threshold |
| --- | --- | --- | --- |
| `action` | `action_text_color` | `action_color` | ≥ 4.5:1 |
| `description` | `description_text_color` | `description_color` | ≥ 4.5:1 |
| `footer` | `footer_text_color` | `footer_color` | ≥ 4.5:1 |
| `link` | `link_color` (`alternative_link_color` or `action_color`) | Page background `#FFFFFF` | ≥ 4.5:1 |

**Null / empty handling (skip = not shown as fail, not included in save warning):**

| Pair | Evaluate only when |
| --- | --- |
| `action` | Both `action_color` and `action_text_color` are set |
| `description` | Both `description_color` and `description_text_color` are set |
| `footer` | Both `footer_color` and `footer_text_color` are set |
| `link` | At least one of `alternative_link_color` or `action_color` is set |

Marlin defaults for empty fields are out of scope until the admin has set both sides of a pair.

## Implementation sketch

### Files (expected)

| Area | Path |
| --- | --- |
| Contrast helpers | `bluebottle/cms/utils/color_contrast.py` (+ tests) |
| Admin wiring | `bluebottle/cms/admin.py` (`Media`, `save_model`) |
| Static assets | e.g. `bluebottle/cms/static/cms/admin/platform_color_contrast.js` (+ CSS) |

### Tests

- Unit tests for Python helper: known pass/fail hex pairs; link falls back to `action_color` when alternative is empty; skips incomplete pairs.
- No Marlin tests in v1.

### i18n

Admin warning and UI strings should be translatable (`gettext`) where they appear in Django templates/messages. Keep copy short.

## Acceptance criteria

1. Editing Styling colors updates ratio badges and the button / link / footer preview without save.
2. Failing AA shows clear Fail state; passing shows Pass.
3. Saving with failing pairs succeeds and shows a Django warning naming those pairs and ratios.
4. Saving with all evaluated pairs passing does not show a contrast warning.
5. Helper tests cover pass, fail, link fallback, and skip-incomplete behavior.
6. No changes required to Marlin or `/api/config` schema for v1.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| JS and Python ratios diverge slightly | Shared fixtures / documented WCAG formula; golden hex pairs in tests for both if practical |
| django-colorfield DOM changes break listeners | Scope selectors carefully; smoke-test admin form after colorfield upgrades |
| Preview oversimplifies real UI (hover shades, `action.100` surfaces) | Document as known limit; defer palette-stop checks to a later phase |
| Admins ignore soft warnings | Preview makes failure visible; revisit hard-block only if policy requires |

## Follow-ups (explicitly deferred)

1. Suggest nearest AA-passing text color (slider / one-click fix).
2. Validate Marlin-derived palette stops used for hover/tinted surfaces.
3. Optional APCA score alongside WCAG (informational).
4. Expose contrast evaluation on `/api/config` for Marlin/devtools.
5. Align segment button colors with the same pair evaluator.
6. Hard-block save under a tenant policy flag (if legal/compliance needs it).

## Sources

- [W3C — Understanding WCAG 2.2 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [W3C — Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- [Shopify Help — Accessibility for themes (color contrast)](https://help.shopify.com/en/manual/online-store/themes/customizing-themes/accessibility)
- [Adrian Roselli — WCAG3 Contrast as of April 2026](https://adrianroselli.com/2026/04/wcag3-contrast-as-of-april-2026.html)
- [Z.Tools — WCAG 2 vs APCA](https://z.tools/blog/apca-vs-wcag-contrast)
- [ChromUI — Accessible UI themes](https://chromui.app/accessibility)
- [Color Safe Palette Builder](https://66colorful.com/tools/color-safe-palette-builder)
- Internal: `bluebottle/segments/models.py` (`text_color`), `bluebottle/cms/models.py` (platform color fields)
