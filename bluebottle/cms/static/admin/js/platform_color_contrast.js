(function () {
    'use strict';

    var CC = window.ColorContrast;
    var WHITE = CC.WHITE;
    var normalizeHex = CC.normalizeHex;
    var mixWithWhite = CC.mixWithWhite;
    var chooseOnColor = CC.chooseOnColor;
    var ensureContrast = CC.ensureContrast;
    var ensureContrastOnSurfaces = CC.ensureContrastOnSurfaces;
    var ensureReadableFill = CC.ensureReadableFill;
    var applySwatch = CC.applySwatch;
    var failsContrast = CC.failsContrast;
    var showDisclaimer = CC.showDisclaimer;

    var PALE_GREY = '#EEEEEE';
    var TINT_STOPS = {
        action: [
            { id: 'tint-200', amount: 90 }
        ],
        description: [
            { id: 'tint-200', amount: 90 }
        ]
    };
    var FIELD_IDS = {
        actionColor: 'id_action_color',
        actionTextColor: 'id_action_text_color',
        descriptionColor: 'id_description_color',
        descriptionTextColor: 'id_description_text_color',
        alternativeLinkColor: 'id_alternative_link_color',
        accessibleColours: 'id_accessible_colours'
    };

    function fieldValue(fieldId) {
        var input = document.getElementById(fieldId);
        if (!input) {
            return null;
        }
        return normalizeHex(input.value);
    }

    function accessibleEnabled() {
        var input = document.getElementById(FIELD_IDS.accessibleColours);
        if (input) {
            return input.checked;
        }
        var panel = document.getElementById('platform-color-contrast-panel');
        return Boolean(panel && panel.getAttribute('data-accessible') === 'true');
    }

    function clearPreview(prefix) {
        applySwatch(prefix + '-solid', null, null, false);
        applySwatch(prefix + '-text', WHITE, null, false);
        TINT_STOPS[prefix].forEach(function (stop) {
            applySwatch(prefix + '-' + stop.id, null, null, false);
        });
    }

    function previewBrandRaw(prefix, brand, textColor, onWhiteColor) {
        if (!brand) {
            clearPreview(prefix);
            return false;
        }
        var solidLow = failsContrast(textColor, brand);
        var textLow = failsContrast(onWhiteColor, WHITE);
        var tintLow = false;
        applySwatch(prefix + '-solid', brand, textColor, solidLow);
        applySwatch(prefix + '-text', WHITE, onWhiteColor, textLow);
        TINT_STOPS[prefix].forEach(function (stop) {
            var tint = mixWithWhite(brand, stop.amount);
            var low = failsContrast(brand, tint);
            applySwatch(prefix + '-' + stop.id, tint, brand, low);
            tintLow = tintLow || low;
        });
        return solidLow || textLow || tintLow;
    }

    function previewBrand(prefix, brand) {
        if (!brand) {
            clearPreview(prefix);
            return false;
        }
        var fill = ensureReadableFill(brand);
        var onSolid = chooseOnColor(fill);
        var onBackground = ensureContrastOnSurfaces(brand, [WHITE, PALE_GREY]);
        var fillAdjusted = fill !== brand;
        var tintAdjusted = false;
        applySwatch(prefix + '-solid', fill, onSolid, fillAdjusted);
        applySwatch(prefix + '-text', WHITE, onBackground, onBackground !== brand);
        TINT_STOPS[prefix].forEach(function (stop) {
            var tint = mixWithWhite(fill, stop.amount);
            var onTint = ensureContrast(fill, tint);
            var altered = fillAdjusted || onTint !== brand;
            applySwatch(prefix + '-' + stop.id, tint, onTint, altered);
            tintAdjusted = tintAdjusted || altered;
        });
        return fillAdjusted || onBackground !== brand || tintAdjusted;
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
