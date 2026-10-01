(function () {
    'use strict';

    var WHITE = '#FFFFFF';
    var DARK_NEUTRAL = '#2A2A2A';
    var DARK_TEXT_RATIO = 7;
    var PALE_GREY = '#EEEEEE';
    var TINT_AMOUNT = 90;
    var TINT_300_AMOUNT = 80;
    var FIELD_IDS = {
        actionColor: 'id_action_color',
        actionTextColor: 'id_action_text_color',
        descriptionColor: 'id_description_color',
        descriptionTextColor: 'id_description_text_color',
        alternativeLinkColor: 'id_alternative_link_color',
        accessibleColours: 'id_accessible_colours'
    };

    function normalizeHex(value) {
        if (!value) {
            return null;
        }
        value = String(value).trim();
        if (!value) {
            return null;
        }
        if (value.charAt(0) !== '#') {
            value = '#' + value;
        }
        if (!/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value)) {
            return null;
        }
        if (value.length === 4) {
            value = '#' + value[1] + value[1] + value[2] + value[2] + value[3] + value[3];
        }
        return value.toUpperCase();
    }

    function channelToLinear(channel) {
        var value = channel / 255;
        if (value <= 0.03928) {
            return value / 12.92;
        }
        return Math.pow((value + 0.055) / 1.055, 2.4);
    }

    function parseRgb(hex) {
        var normalized = normalizeHex(hex);
        return {
            r: parseInt(normalized.slice(1, 3), 16),
            g: parseInt(normalized.slice(3, 5), 16),
            b: parseInt(normalized.slice(5, 7), 16)
        };
    }

    function hexFromRgb(r, g, b) {
        function pad(value) {
            var hex = Math.round(Math.max(0, Math.min(255, value))).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }
        return ('#' + pad(r) + pad(g) + pad(b)).toUpperCase();
    }

    function relativeLuminance(hex) {
        var rgb = parseRgb(hex);
        return (
            0.2126 * channelToLinear(rgb.r) +
            0.7152 * channelToLinear(rgb.g) +
            0.0722 * channelToLinear(rgb.b)
        );
    }

    function contrastRatio(foreground, background) {
        var l1 = relativeLuminance(foreground);
        var l2 = relativeLuminance(background);
        var lighter = Math.max(l1, l2);
        var darker = Math.min(l1, l2);
        return (lighter + 0.05) / (darker + 0.05);
    }

    function passesAa(ratio) {
        return ratio >= 4.5;
    }

    function mixWithWhite(hex, amount) {
        var rgb = parseRgb(hex);
        var weight = amount / 100;
        return hexFromRgb(
            (255 - rgb.r) * weight + rgb.r,
            (255 - rgb.g) * weight + rgb.g,
            (255 - rgb.b) * weight + rgb.b
        );
    }

    function mixWithBlack(hex, amount) {
        var rgb = parseRgb(hex);
        var keep = 1 - amount / 100;
        return hexFromRgb(rgb.r * keep, rgb.g * keep, rgb.b * keep);
    }

    function chooseOnColor(background) {
        background = normalizeHex(background);
        if (!background) {
            return null;
        }
        var whiteRatio = contrastRatio(WHITE, background);
        var darkRatio = contrastRatio(DARK_NEUTRAL, background);
        var whitePass = passesAa(whiteRatio);
        var darkPass = passesAa(darkRatio);
        if (whitePass && !darkPass) {
            return WHITE;
        }
        if (darkPass && !whitePass) {
            return DARK_NEUTRAL;
        }
        return whiteRatio >= darkRatio ? WHITE : DARK_NEUTRAL;
    }

    function ensureContrast(foreground, background) {
        foreground = normalizeHex(foreground);
        background = normalizeHex(background);
        if (!foreground || !background) {
            return null;
        }
        if (passesAa(contrastRatio(foreground, background))) {
            return foreground;
        }
        var low = 1;
        var high = 100;
        var best = null;
        while (low <= high) {
            var mid = Math.floor((low + high) / 2);
            var candidate = mixWithBlack(foreground, mid);
            if (passesAa(contrastRatio(candidate, background))) {
                best = candidate;
                high = mid - 1;
            } else {
                low = mid + 1;
            }
        }
        return best || DARK_NEUTRAL;
    }

    function ensureContrastOnSurfaces(foreground, backgrounds) {
        var result = normalizeHex(foreground);
        if (!result) {
            return null;
        }
        backgrounds.forEach(function (background) {
            result = ensureContrast(result, background);
        });
        return result;
    }

    function fieldValue(fieldId) {
        var input = document.getElementById(fieldId);
        if (!input) {
            return null;
        }
        return normalizeHex(input.value);
    }

    function ensureReadableFill(fill) {
        fill = normalizeHex(fill);
        if (!fill) {
            return null;
        }
        if (passesAa(contrastRatio(WHITE, fill)) || contrastRatio(DARK_NEUTRAL, fill) >= DARK_TEXT_RATIO) {
            return fill;
        }
        var low = 1;
        var high = 100;
        var best = null;
        while (low <= high) {
            var mid = Math.floor((low + high) / 2);
            var candidate = mixWithBlack(fill, mid);
            if (passesAa(contrastRatio(WHITE, candidate))) {
                best = candidate;
                high = mid - 1;
            } else {
                low = mid + 1;
            }
        }
        return best || '#000000';
    }

    function applySwatch(name, background, color, altered) {
        var root = document.querySelector('[data-preview="' + name + '"]');
        if (!root) {
            return;
        }
        var sample = root.querySelector('.platform-color-contrast__sample');
        if (!sample) {
            return;
        }
        sample.style.backgroundColor = background || '#f5f5f5';
        sample.style.color = color || '#666666';
        var mark = root.querySelector('.platform-color-contrast__mark');
        if (mark) {
            mark.hidden = !altered;
        }
    }

    function accessibleEnabled() {
        var input = document.getElementById(FIELD_IDS.accessibleColours);
        if (input) {
            return input.checked;
        }
        var panel = document.getElementById('platform-color-contrast-panel');
        return Boolean(panel && panel.getAttribute('data-accessible') === 'true');
    }

    function failsContrast(foreground, background) {
        if (!foreground || !background) {
            return false;
        }
        return !passesAa(contrastRatio(foreground, background));
    }

    function showDisclaimer(kind, visible) {
        var note = document.querySelector('[data-disclaimer="' + kind + '"]');
        if (note) {
            note.hidden = !visible;
        }
    }

    function previewBrandRaw(prefix, brand, textColor, onWhiteColor) {
        if (!brand) {
            applySwatch(prefix + '-solid', null, null, false);
            applySwatch(prefix + '-text', WHITE, null, false);
            applySwatch(prefix + '-tint', null, null, false);
            applySwatch(prefix + '-tint-300', null, null, false);
            return false;
        }
        var tint = mixWithWhite(brand, TINT_AMOUNT);
        var tint300 = mixWithWhite(brand, TINT_300_AMOUNT);
        var solidLow = failsContrast(textColor, brand);
        var textLow = failsContrast(onWhiteColor, WHITE);
        var tintLow = failsContrast(brand, tint);
        var tint300Low = failsContrast(brand, tint300);
        applySwatch(prefix + '-solid', brand, textColor, solidLow);
        applySwatch(prefix + '-text', WHITE, onWhiteColor, textLow);
        applySwatch(prefix + '-tint', tint, brand, tintLow);
        applySwatch(prefix + '-tint-300', tint300, brand, tint300Low);
        return solidLow || textLow || tintLow || tint300Low;
    }

    function previewBrand(prefix, brand) {
        if (!brand) {
            applySwatch(prefix + '-solid', null, null, false);
            applySwatch(prefix + '-text', WHITE, null, false);
            applySwatch(prefix + '-tint', null, null, false);
            applySwatch(prefix + '-tint-300', null, null, false);
            return false;
        }
        var fill = ensureReadableFill(brand);
        var onSolid = chooseOnColor(fill);
        var onBackground = ensureContrastOnSurfaces(brand, [WHITE, PALE_GREY]);
        var tint = mixWithWhite(fill, TINT_AMOUNT);
        var onTint = ensureContrast(fill, tint);
        var tint300 = mixWithWhite(fill, TINT_300_AMOUNT);
        var onTint300 = ensureContrast(fill, tint300);
        var fillAdjusted = fill !== brand;
        applySwatch(prefix + '-solid', fill, onSolid, fillAdjusted);
        applySwatch(prefix + '-text', WHITE, onBackground, onBackground !== brand);
        applySwatch(prefix + '-tint', tint, onTint, fillAdjusted || onTint !== brand);
        applySwatch(prefix + '-tint-300', tint300, onTint300, fillAdjusted || onTint300 !== brand);
        return fillAdjusted || onBackground !== brand || onTint !== brand || onTint300 !== brand;
    }

    function update() {
        var accessible = accessibleEnabled();
        var actionFlagged;
        var descriptionFlagged;
        if (accessible) {
            actionFlagged = previewBrand('action', fieldValue(FIELD_IDS.actionColor));
            descriptionFlagged = previewBrand('description', fieldValue(FIELD_IDS.descriptionColor));
        } else {
            actionFlagged = previewBrandRaw(
                'action',
                fieldValue(FIELD_IDS.actionColor),
                fieldValue(FIELD_IDS.actionTextColor),
                fieldValue(FIELD_IDS.alternativeLinkColor)
            );
            descriptionFlagged = previewBrandRaw(
                'description',
                fieldValue(FIELD_IDS.descriptionColor),
                fieldValue(FIELD_IDS.descriptionTextColor),
                fieldValue(FIELD_IDS.descriptionColor)
            );
        }
        var flagged = actionFlagged || descriptionFlagged;
        showDisclaimer('adjusted', accessible && flagged);
        showDisclaimer('contrast', !accessible && flagged);
    }

    function bind() {
        var panel = document.getElementById('platform-color-contrast-panel');
        if (!panel) {
            return;
        }

        Object.keys(FIELD_IDS).forEach(function (key) {
            var input = document.getElementById(FIELD_IDS[key]);
            if (!input) {
                return;
            }
            input.addEventListener('input', update);
            input.addEventListener('change', update);
        });

        update();
        window.setInterval(update, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();
