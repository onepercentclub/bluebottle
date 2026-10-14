(function () {
    'use strict';

    var WHITE = '#FFFFFF';
    var DARK_NEUTRAL = '#2A2A2A';
    var DARK_TEXT_RATIO = 7;
    var COLOR_FIELD_ID = 'id_color';

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

    function applySwatch(background, color, altered) {
        var root = document.querySelector('[data-preview="organization-solid"]');
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
        var panel = document.getElementById('organization-color-contrast-panel');
        return Boolean(panel && panel.getAttribute('data-accessible') === 'true');
    }

    function showDisclaimer(kind, visible) {
        var note = document.querySelector(
            '#organization-color-contrast-panel [data-disclaimer="' + kind + '"]'
        );
        if (note) {
            note.hidden = !visible;
        }
    }

    function fieldValue() {
        var input = document.getElementById(COLOR_FIELD_ID);
        if (!input) {
            return null;
        }
        return normalizeHex(input.value);
    }

    function update() {
        var brand = fieldValue();
        var accessible = accessibleEnabled();
        if (!brand) {
            applySwatch(null, null, false);
            showDisclaimer('adjusted', false);
            showDisclaimer('contrast', false);
            return;
        }
        if (accessible) {
            var fill = ensureReadableFill(brand);
            var onSolid = chooseOnColor(fill);
            var fillAdjusted = fill !== brand;
            applySwatch(fill, onSolid, fillAdjusted);
            showDisclaimer('adjusted', fillAdjusted);
            showDisclaimer('contrast', false);
            return;
        }
        var textColor = chooseOnColor(brand);
        var solidLow = !passesAa(contrastRatio(textColor, brand));
        applySwatch(brand, textColor, solidLow);
        showDisclaimer('adjusted', false);
        showDisclaimer('contrast', solidLow);
    }

    function bind() {
        var panel = document.getElementById('organization-color-contrast-panel');
        if (!panel) {
            return;
        }

        var input = document.getElementById(COLOR_FIELD_ID);
        if (input) {
            input.addEventListener('input', update);
            input.addEventListener('change', update);
        }

        update();
        window.setInterval(update, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();
