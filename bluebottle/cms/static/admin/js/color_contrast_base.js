(function (global) {
    'use strict';

    var WHITE = '#FFFFFF';
    var DARK_NEUTRAL = '#2A2A2A';
    var DARK_TEXT_RATIO = 7;

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

    global.ColorContrast = {
        WHITE: WHITE,
        normalizeHex: normalizeHex,
        contrastRatio: contrastRatio,
        passesAa: passesAa,
        mixWithWhite: mixWithWhite,
        chooseOnColor: chooseOnColor,
        ensureContrast: ensureContrast,
        ensureContrastOnSurfaces: ensureContrastOnSurfaces,
        ensureReadableFill: ensureReadableFill,
        applySwatch: applySwatch,
        failsContrast: failsContrast,
        showDisclaimer: showDisclaimer
    };
})(window);
