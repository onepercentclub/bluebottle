(function () {
    var lastPlaceId = null;
    var debug = true

    function log() {
        if (!debug || typeof console === 'undefined' || !console.log) return;
        // eslint-disable-next-line no-console
        console.log.apply(console, arguments);
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
        const mapbox_id = place.properties.mapbox_id;
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
})();
