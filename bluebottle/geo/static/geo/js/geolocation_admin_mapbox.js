(function () {
    var lastPlaceId = null;
    var debug =
        window &&
        window.location &&
        window.location.search &&
        window.location.search.indexOf('geo_debug=1') !== -1;

    function log() {
        if (!debug || typeof console === 'undefined' || !console.log) return;
        // eslint-disable-next-line no-console
        console.log.apply(console, arguments);
    }

    function t(text) {
        if (typeof window.gettext === 'function') return window.gettext(text);
        return text;
    }

    function setText(root, selector, text) {
        var el = root.querySelector(selector);
        if (!el) return;
        el.textContent = text;
    }

    function setPlaceholder(root, selector, text) {
        var el = root.querySelector(selector);
        if (!el) return;
        el.setAttribute('placeholder', text);
        el.setAttribute('aria-label', text);
    }

    function translateMapWidgetUI() {
        var wrap = document.querySelector('#position-mw-wrap');
        if (!wrap) return false;

        // Buttons
        setText(wrap, '.mw-btn-add-marker .button-text', t('Point on Map'));
        setText(wrap, '.mw-btn-my-location .button-text', t('Current Location'));
        setText(wrap, '.mw-btn-coordinates .button-text', t('Edit Coordinates'));
        setText(wrap, '.mw-btn-coordinates-done', t('Done'));

        // Help text
        setText(
            wrap,
            '.mw-help-text',
            t('Place the pin or type address where you want point on the map')
        );

        // Placeholders (geocoder + coordinate overlay)
        setPlaceholder(wrap, '.mapboxgl-ctrl-geocoder--input', t('Find a Location by Address'));
        setPlaceholder(wrap, '.mw-overlay-latitude', t('Ex: 41.015137'));
        setPlaceholder(wrap, '.mw-overlay-longitude', t('Ex: 28.979530'));

        return true;
    }

    function getPreferredJQuery() {
        // IMPORTANT: Mapwidgets triggers events using mapWidgets.jQuery.
        if (window.mapWidgets && window.mapWidgets.jQuery) return window.mapWidgets.jQuery;
        if (window.django && window.django.jQuery) return window.django.jQuery;
        if (window.jQuery) return window.jQuery;
        return null;
    }

    function findMapboxIdInput() {
        return (
            document.querySelector('#id_mapbox_id') ||
            document.querySelector('input[name="mapbox_id"]') ||
            document.querySelector('input[name$="-mapbox_id"]')
        );
    }

    function extractPlaceFromArgs(args) {
        // args[0] is the event. The rest can vary by mapwidgets version.
        for (var i = 1; i < args.length; i += 1) {
            var candidate = args[i];
            if (candidate && typeof candidate === 'object' && candidate.id) {
                return candidate;
            }
        }
        return null;
    }

    function handlePlaceChanged() {
        var place = extractPlaceFromArgs(arguments);
        log('[geo admin] place changed args', arguments);
        var mapbox_id = (place.properties && place.properties.mapbox_id) || (place && place.id);
        if (!mapbox_id) return;

        log('[geo admin] found', place);

        lastPlaceId = mapbox_id;
        var mapboxIdInput = findMapboxIdInput();
        if (mapboxIdInput) {
            mapboxIdInput.value = mapbox_id;
            log('[geo admin] set mapbox_id', mapbox_id);
        }
        var formattedAddressInput = document.querySelector('#id_formatted_address');
        if (formattedAddressInput && place.place_name) {
            formattedAddressInput.value = place.place_name;
        }
    }

    var boundWith = null;

    function bindHandlers() {
        var $ = getPreferredJQuery();
        if (!$) {
            log('[geo admin] no jquery found yet');
            return false;
        }

        var bindingName =
            $ === (window.mapWidgets && window.mapWidgets.jQuery)
                ? 'mapWidgets.jQuery'
                : $ === (window.django && window.django.jQuery)
                    ? 'django.jQuery'
                    : 'window.jQuery';

        // If we already bound with mapWidgets.jQuery, don't bind again.
        if (boundWith === 'mapWidgets.jQuery' && bindingName === 'mapWidgets.jQuery') {
            return true;
        }

        // Mapwidget emits these when the built-in geocoder changes.
        $(document).on('mapboxPointFieldWidget:placeChanged', handlePlaceChanged);
        // Backwards compat for older trigger names
        $(document).on('mapbox_point_map_widget:place_changed', handlePlaceChanged);

        // Safety net: ensure mapbox_id is posted on submit.
        $(document).on('submit', 'form#geolocation_form', function () {
            var mapboxIdInput = findMapboxIdInput();
            log('[geo admin] submit', {mapboxId: mapboxIdInput && mapboxIdInput.value, lastPlaceId: lastPlaceId});
            if (mapboxIdInput && (!mapboxIdInput.value || mapboxIdInput.value === 'unknown') && lastPlaceId) {
                mapboxIdInput.value = lastPlaceId;
            }
        });

        boundWith = bindingName;
        log('[geo admin] handlers bound using', bindingName);
        return true;
    }

    // Script can be loaded before mapwidgets init. Bind now (best effort),
    // then bind again on load to ensure we eventually bind with mapWidgets.jQuery.
    bindHandlers();
    window.addEventListener('load', function () {
        bindHandlers();
    });

    // Translate the map widget UI once it exists. Mapwidgets creates the DOM after init,
    // so we retry a few times.
    (function translateWhenReady() {
        var attempts = 0;
        var timer = window.setInterval(function () {
            attempts += 1;
            if (translateMapWidgetUI() || attempts >= 20) {
                window.clearInterval(timer);
            }
        }, 250);
    })();
})();
