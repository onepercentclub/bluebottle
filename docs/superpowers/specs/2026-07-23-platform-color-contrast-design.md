# Platform color contrast accessibility — design

**Date:** 2026-07-23  
**Status:** Superseded (audit-first)  
**Primary repo:** bluebottle (Django admin / platform settings)  
**Consuming app:** marlin

## Pivot

The soft-warning admin UX that was drafted/prototyped here is **not** the chosen direction.

Product intent (updated):

- Text must remain readable under **WCAG AA** contrast minimum ([Understanding](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html), [SC 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum)).
- First deliverable: inventory of current failures + awkward design patterns + backlog.
- Later: prevent failures (e.g. theme auto-fallbacks) and fix structural issues (e.g. action colour stacked on description colour).

**Canonical doc:**  
`/home/pieter/Development/marlin/docs/superpowers/specs/2026-07-23-platform-color-contrast-audit.md`

## Historical note (v1 experiment — not the product solution)

An admin live preview + soft save warning for four colour pairs was prototyped in Bluebottle (`cms/utils/color_contrast.py`, admin Media JS/CSS). That only covers stored fill↔text pairs and does not address hardcoded `white`, brand-as-text on white, palette stops, or cross-role stacks. Keep or remove that code separately; do not treat it as completing this initiative.
