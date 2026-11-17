(function () {
    'use strict';

    var CC = window.ColorContrast;

    function update(panel, input) {
        var preview = panel.getAttribute('data-preview-name');
        var accessible = panel.getAttribute('data-accessible') === 'true';
        var brand = CC.normalizeHex(input.value);
        var adjusted = false;
        var lowContrast = false;

        if (!brand) {
            CC.applySwatch(preview, null, null, false);
        } else if (accessible) {
            var fill = CC.ensureReadableFill(brand);
            adjusted = fill !== brand;
            CC.applySwatch(preview, fill, CC.chooseOnColor(fill), adjusted);
        } else {
            var textColor = CC.chooseOnColor(brand);
            lowContrast = CC.failsContrast(textColor, brand);
            CC.applySwatch(preview, brand, textColor, lowContrast);
        }
        CC.showDisclaimer('adjusted', adjusted);
        CC.showDisclaimer('contrast', lowContrast);
    }

    function bind() {
        var panel = document.querySelector('.platform-color-contrast[data-field-id]');
        if (!panel) {
            return;
        }
        var input = document.getElementById(panel.getAttribute('data-field-id'));
        if (!input) {
            return;
        }
        var run = function () {
            update(panel, input);
        };
        input.addEventListener('input', run);
        input.addEventListener('change', run);
        run();
        window.setInterval(run, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else {
        bind();
    }
})();
