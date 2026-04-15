(function () {
    var debug = window && window.location && window.location.search && window.location.search.indexOf('geo_debug=1') !== -1;

    function log() {
        if (!debug || typeof console === 'undefined' || !console.log) return;
        // eslint-disable-next-line no-console
        console.log.apply(console, arguments);
    }

    var lastMapboxId = null;

    function findMapboxIdInput(form) {
        return (
            form.querySelector('input[name="mapbox_id"]') ||
            form.querySelector('input[name$="-mapbox_id"]') ||
            form.querySelector('#id_mapbox_id')
        );
    }

    function mountGeocoderOnSearchInput(form) {
        var searchInput = document.querySelector('#id_mapbox_search');
        if (!searchInput) {
            log('[geo admin] no #id_mapbox_search found, skipping geocoder mount');
            return;
        }

        var token = searchInput.getAttribute('data-mapbox-access-token');
        if (!token) {
            log('[geo admin] no mapbox access token on search input');
            return;
        }
        if (typeof MapboxGeocoder === 'undefined') {
            log('[geo admin] MapboxGeocoder not loaded yet');
            return;
        }

        var geocoder = new MapboxGeocoder({
            accessToken: token,
            marker: false,
            mapboxgl: typeof mapboxgl !== 'undefined' ? mapboxgl : undefined,
            placeholder: searchInput.getAttribute('placeholder') || 'Search…',
            types: 'country,region,district,place,locality,postcode,address',
        });

        // Render geocoder UI into the existing input's parent and hide the original.
        var wrapper = document.createElement('div');
        wrapper.className = 'mapbox-geocoder-admin';
        searchInput.parentNode.insertBefore(wrapper, searchInput);
        wrapper.appendChild(geocoder.onAdd());

        searchInput.style.display = 'none';
        log('[geo admin] geocoder mounted');

        geocoder.on('result', function (ev) {
            var place = ev && ev.result;
            if (!place || !place.id) {
                log('[geo admin] geocoder result without id', place);
                return;
            }
            lastMapboxId = place.id;
            var mapboxIdInput = findMapboxIdInput(form);
            if (mapboxIdInput) {
                mapboxIdInput.value = place.id;
                log('[geo admin] set mapbox_id', place.id);
            } else {
                log('[geo admin] could not find mapbox_id input');
            }
        });
    }

    if (typeof django === 'undefined' || !django.jQuery) {
        return;
    }

    django.jQuery(function () {
        var form = document.querySelector('#content form');
        if (!form) {
            log('[geo admin] no form found on page');
            return;
        }
        mountGeocoderOnSearchInput(form);
    });

    // Safety net: ensure mapbox_id is filled on submit.
    django.jQuery(document).on('submit', 'form', function () {
        var form = this;
        var mapboxIdInput = findMapboxIdInput(form);
        if (mapboxIdInput && (!mapboxIdInput.value || mapboxIdInput.value === 'unknown') && lastMapboxId) {
            mapboxIdInput.value = lastMapboxId;
            log('[geo admin] submit fallback set mapbox_id', lastMapboxId);
        } else {
            log('[geo admin] submit', {
                hasMapboxIdInput: Boolean(mapboxIdInput),
                mapboxId: mapboxIdInput && mapboxIdInput.value,
                lastMapboxId: lastMapboxId,
            });
        }
    });
})();
