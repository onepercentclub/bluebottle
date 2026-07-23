(function () {
    'use strict';

    var PAGE_BACKGROUND = '#FFFFFF';
    var FIELD_IDS = {
        actionColor: 'id_action_color',
        actionTextColor: 'id_action_text_color',
        alternativeLinkColor: 'id_alternative_link_color',
        descriptionColor: 'id_description_color',
        descriptionTextColor: 'id_description_text_color',
        footerColor: 'id_footer_color',
        footerTextColor: 'id_footer_text_color'
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

    function relativeLuminance(hex) {
        var normalized = normalizeHex(hex);
        var r = parseInt(normalized.slice(1, 3), 16);
        var g = parseInt(normalized.slice(3, 5), 16);
        var b = parseInt(normalized.slice(5, 7), 16);
        return (
            0.2126 * channelToLinear(r) +
            0.7152 * channelToLinear(g) +
            0.0722 * channelToLinear(b)
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

    function fieldValue(fieldId) {
        var input = document.getElementById(fieldId);
        if (!input) {
            return null;
        }
        return normalizeHex(input.value);
    }

    function linkColor() {
        return fieldValue(FIELD_IDS.alternativeLinkColor) || fieldValue(FIELD_IDS.actionColor);
    }

    function setPairState(pairId, foreground, background) {
        var row = document.querySelector('[data-contrast-pair="' + pairId + '"]');
        if (!row) {
            return;
        }
        var ratioEl = row.querySelector('[data-contrast-ratio]');
        var badgeEl = row.querySelector('[data-contrast-badge]');
        var hintEl = row.querySelector('[data-contrast-hint]');

        if (!foreground || !background) {
            row.classList.remove('is-pass', 'is-fail');
            row.classList.add('is-skipped');
            if (ratioEl) {
                ratioEl.textContent = '—';
            }
            if (badgeEl) {
                badgeEl.textContent = 'Not set';
            }
            if (hintEl) {
                hintEl.hidden = true;
            }
            return;
        }

        var ratio = contrastRatio(foreground, background);
        var passes = passesAa(ratio);
        row.classList.remove('is-skipped', 'is-pass', 'is-fail');
        row.classList.add(passes ? 'is-pass' : 'is-fail');
        if (ratioEl) {
            ratioEl.textContent = ratio.toFixed(1) + ':1';
        }
        if (badgeEl) {
            badgeEl.textContent = passes ? 'Pass AA' : 'Fail AA';
        }
        if (hintEl) {
            hintEl.hidden = passes;
        }
    }

    function applyFilledPreview(selector, background, color) {
        var el = document.querySelector(selector);
        if (!el) {
            return;
        }
        el.style.backgroundColor = background || '#f5f5f5';
        el.style.color = color || '#666666';
    }

    function applyLinkPreview(color) {
        var el = document.querySelector('.platform-color-contrast__link');
        if (!el) {
            return;
        }
        el.style.backgroundColor = PAGE_BACKGROUND;
        el.style.color = color || '#666666';
    }

    function update() {
        var actionColor = fieldValue(FIELD_IDS.actionColor);
        var actionText = fieldValue(FIELD_IDS.actionTextColor);
        var descriptionColor = fieldValue(FIELD_IDS.descriptionColor);
        var descriptionText = fieldValue(FIELD_IDS.descriptionTextColor);
        var footerColor = fieldValue(FIELD_IDS.footerColor);
        var footerText = fieldValue(FIELD_IDS.footerTextColor);
        var link = linkColor();

        setPairState('action', actionText, actionColor);
        setPairState('description', descriptionText, descriptionColor);
        setPairState('footer', footerText, footerColor);
        setPairState('link', link, PAGE_BACKGROUND);

        applyFilledPreview('.platform-color-contrast__button', actionColor, actionText);
        applyFilledPreview('.platform-color-contrast__description', descriptionColor, descriptionText);
        applyFilledPreview('.platform-color-contrast__footer', footerColor, footerText);
        applyLinkPreview(link);
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
