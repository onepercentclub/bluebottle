(function () {
    var debug = window && window.location && window.location.search && window.location.search.indexOf('geo_debug=1') !== -1;

    function log() {
        if (!debug || typeof console === 'undefined' || !console.log) return;
        // eslint-disable-next-line no-console
        console.log.apply(console, arguments);
    }

    var lastMapboxId = null;
    var lastCenter = null;

    function findMapboxIdInput(form) {
        return (
            form.querySelector('input[name="mapbox_id"]') ||
            form.querySelector('input[name$="-mapbox_id"]') ||
            form.querySelector('#id_mapbox_id')
        );
    }

    function findPositionInput(form) {
        return (
            form.querySelector('textarea[name="position"]') ||
            form.querySelector('input[name="position"]') ||
            form.querySelector('textarea[name$="-position"]') ||
            form.querySelector('input[name$="-position"]') ||
            form.querySelector('#id_position')
        );
    }

    function findLatitudeInput(form) {
        return (
            form.querySelector('input[name="latitude"]') ||
            form.querySelector('input[name$="-latitude"]') ||
            form.querySelector('#id_latitude')
        );
    }

    function findLongitudeInput(form) {
        return (
            form.querySelector('input[name="longitude"]') ||
            form.querySelector('input[name$="-longitude"]') ||
            form.querySelector('#id_longitude')
        );
    }

    function setPositionFromCenter(form, center) {
        if (!center || center.length !== 2) return;
        var lon = center[0];
        var lat = center[1];
        if (typeof lon !== 'number' || typeof lat !== 'number') return;

        var latitudeInput = findLatitudeInput(form);
        if (latitudeInput) latitudeInput.value = lat;
        var longitudeInput = findLongitudeInput(form);
        if (longitudeInput) longitudeInput.value = lon;

        var positionInput = findPositionInput(form);
        if (!positionInput) {
            log('[geo admin] could not find position input');
            return;
        }

        // GeoDjango PointField admin typically stores WKT: "POINT (lon lat)"
        positionInput.value = 'POINT (' + lon + ' ' + lat + ')';
        lastCenter = [lon, lat];
        log('[geo admin] set position', positionInput.value);

        // Trigger change for any admin JS that listens to it.
        if (typeof django !== 'undefined' && django.jQuery) {
            django.jQuery(positionInput).trigger('change');
        }
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

            // Also store coordinates so backend can derive street/number.
            var center = place.center;
            if ((!center || center.length !== 2) && place.geometry && place.geometry.coordinates) {
                center = place.geometry.coordinates;
            }
            if (center && center.length === 2) {
                setPositionFromCenter(form, center);
            } else {
                log('[geo admin] no coordinates in geocoder result', place);
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
        }
        var positionInput = findPositionInput(form);
        if (
            positionInput &&
            (!positionInput.value || positionInput.value === 'unknown') &&
            lastCenter &&
            lastCenter.length === 2
        ) {
            positionInput.value = 'POINT (' + lastCenter[0] + ' ' + lastCenter[1] + ')';
            log('[geo admin] submit fallback set position', positionInput.value);
        } else {
            log('[geo admin] submit', {
                hasMapboxIdInput: Boolean(mapboxIdInput),
                mapboxId: mapboxIdInput && mapboxIdInput.value,
                lastMapboxId: lastMapboxId,
                position: positionInput && positionInput.value,
                lastCenter: lastCenter,
            });
        }
    });
})();
