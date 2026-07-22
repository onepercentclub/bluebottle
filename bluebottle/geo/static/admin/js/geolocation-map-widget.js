(function ($) {
    'use strict';

    function preferAddressFeature(features) {
        if (!features || !features.length) {
            return null;
        }
        for (let index = 0; index < features.length; index += 1) {
            const feature = features[index];
            if (feature.properties && feature.properties.feature_type === 'address') {
                return feature;
            }
        }
        return features[0];
    }

    function featureLabel(feature) {
        const properties = feature.properties || {};
        return properties.full_address
            || [properties.name, properties.place_formatted].filter(Boolean).join(', ')
            || properties.name
            || '';
    }

    function setMapboxId(mapboxId) {
        const field = document.getElementById('id_mapbox_id');
        if (field) {
            field.value = mapboxId || '';
        }
    }

    function getExistingMapboxId() {
        const field = document.getElementById('id_mapbox_id');
        return field && field.value ? field.value.trim() : '';
    }

    function getExistingLocationName() {
        const field = document.getElementById('id_location_name');
        return field && field.value ? field.value.trim() : '';
    }

    function forwardGeocodeByMapboxIdV6(mapboxId, accessToken) {
        const url = new URL('https://api.mapbox.com/search/geocode/v6/forward');
        url.searchParams.set('q', mapboxId);
        url.searchParams.set('permanent', 'true');
        url.searchParams.set('limit', '1');
        url.searchParams.set('access_token', accessToken);

        return fetch(url.toString())
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                return preferAddressFeature(data.features || []);
            });
    }

    function loadExistingGeolocation(widget) {
        const latitude = widget.djangoGeoJSONValue.lat;
        const longitude = widget.djangoGeoJSONValue.lng;
        const mapboxId = getExistingMapboxId();
        const locationName = getExistingLocationName();

        function showMarker(displayLatitude, displayLongitude) {
            widget.addMarkerToMap(displayLatitude, displayLongitude);
            widget.fitBoundMarker();
            widget.enableClearBtn();
            if (widget.addressAutoCompleteInput) {
                widget.addressAutoCompleteInput.val(locationName);
            }
        }

        if (mapboxId) {
            forwardGeocodeByMapboxIdV6(mapboxId, mapboxgl.accessToken).then(function (feature) {
                if (feature && feature.geometry && feature.geometry.coordinates) {
                    const coordinates = feature.geometry.coordinates;
                    showMarker(coordinates[1], coordinates[0]);
                    if (widget.addressAutoCompleteInput && !locationName) {
                        widget.addressAutoCompleteInput.val(featureLabel(feature));
                    }
                } else {
                    showMarker(latitude, longitude);
                }
            });
            return;
        }

        showMarker(latitude, longitude);
    }

    function buildReverseUrl(longitude, latitude, accessToken, types, limit) {
        const url = new URL('https://api.mapbox.com/search/geocode/v6/reverse');
        url.searchParams.set('longitude', longitude);
        url.searchParams.set('latitude', latitude);
        url.searchParams.set('permanent', 'true');
        url.searchParams.set('access_token', accessToken);
        if (types) {
            url.searchParams.set('types', types);
            if (limit) {
                url.searchParams.set('limit', limit);
            }
        }
        return url.toString();
    }

    function reverseGeocodeV6(longitude, latitude, accessToken) {
        return fetch(buildReverseUrl(longitude, latitude, accessToken, 'address', '1'))
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                const feature = preferAddressFeature(data.features || []);
                if (feature) {
                    return feature;
                }
                return fetch(buildReverseUrl(longitude, latitude, accessToken))
                    .then(function (response) {
                        return response.json();
                    })
                    .then(function (fallbackData) {
                        return preferAddressFeature(fallbackData.features || []);
                    });
            });
    }

    function forwardGeocodeV6(query, accessToken) {
        const url = new URL('https://api.mapbox.com/search/geocode/v6/forward');
        url.searchParams.set('q', query);
        url.searchParams.set('types', 'address,street,place,locality');
        url.searchParams.set('permanent', 'true');
        url.searchParams.set('limit', '5');
        url.searchParams.set('autocomplete', 'true');
        url.searchParams.set('access_token', accessToken);

        return fetch(url.toString())
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                return data.features || [];
            });
    }

    function createV6Geocoder(widget) {
        const wrap = document.getElementById(widget.geocoderWrapID);
        if (!wrap) {
            return;
        }

        wrap.innerHTML = '';

        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = widget.geocoderInputPlaceholderText || 'Find a Location by Address';
        input.className = 'mapboxgl-ctrl-geocoder--input';
        input.style.width = '100%';

        const list = document.createElement('div');
        list.className = 'geolocation-v6-suggestions';
        list.style.display = 'none';
        list.style.background = '#fff';
        list.style.border = '1px solid #ccc';
        list.style.position = 'absolute';
        list.style.zIndex = '1000';
        list.style.width = '100%';

        wrap.appendChild(input);
        wrap.appendChild(list);
        widget.addressAutoCompleteInput = $(input);

        let debounceTimer = null;

        function hideSuggestions() {
            list.style.display = 'none';
            list.innerHTML = '';
        }

        function selectFeature(feature) {
            const coordinates = feature.geometry.coordinates;
            const longitude = coordinates[0];
            const latitude = coordinates[1];
            input.value = featureLabel(feature);
            hideSuggestions();
            widget.addMarkerToMap(latitude, longitude);
            widget.updateDjangoInput(feature);
            widget.fitBoundMarker();
            setMapboxId(feature.properties.mapbox_id);
            $(document).trigger(
                widget.placeChangedTriggerNameSpace,
                [feature, latitude, longitude, widget.wrapElemSelector, widget.locationInput]
            );
        }

        input.addEventListener('input', function () {
            const query = input.value.trim();
            window.clearTimeout(debounceTimer);

            if (!query) {
                hideSuggestions();
                return;
            }

            debounceTimer = window.setTimeout(function () {
                forwardGeocodeV6(query, mapboxgl.accessToken).then(function (features) {
                    list.innerHTML = '';
                    features.forEach(function (feature) {
                        const item = document.createElement('div');
                        item.textContent = featureLabel(feature);
                        item.style.padding = '8px';
                        item.style.cursor = 'pointer';
                        item.addEventListener('mousedown', function (event) {
                            event.preventDefault();
                            selectFeature(feature);
                        });
                        list.appendChild(item);
                    });
                    list.style.display = features.length ? 'block' : 'none';
                });
            }, 300);
        });

        input.addEventListener('blur', function () {
            window.setTimeout(hideSuggestions, 200);
        });
    }

    function patchMapboxWidget() {
        if (!window.DjangoMapboxPointFieldWidget) {
            window.setTimeout(patchMapboxWidget, 50);
            return;
        }

    DjangoMapboxPointFieldWidget.prototype.init = function (options) {
        $.extend(this, options);
        this.coordinatesOverlayToggleBtn.on('click', this.toggleCoordinatesOverlay.bind(this));
        this.coordinatesOverlayDoneBtn.on('click', this.handleCoordinatesOverlayDoneBtnClick.bind(this));
        this.coordinatesOverlayInputs.on('change', this.handleCoordinatesInputsChange.bind(this));
        this.addMarkerBtn.on('click', this.handleAddMarkerBtnClick.bind(this));
        this.myLocationBtn.on('click', this.handleMyLocationBtnClick.bind(this));
        this.deleteBtn.on('click', this.resetMap.bind(this));

        if ($(this.wrapElemSelector).closest('.module.collapse').length) {
            $(document).on('show.fieldset', this.initializeMap.bind(this));
        }

        mapboxgl.accessToken = this.mapOptions.accessToken;
        this.mapboxOptions = this.mapOptions.mapOptions || {};
        this.mapboxOptions.container = this.mapElement.id;
        this.geocoderOptions = this.mapOptions.geocoderOptions || {};
        if (!this.geocoderOptions.placeholder) {
            this.geocoderOptions.placeholder = this.geocoderInputPlaceholderText;
        }
        this.flyToEnabled = this.geocoderOptions.flyTo || false;

        if (this.mapboxOptions.center) {
            this.mapboxOptions.center = [this.mapboxOptions.center[1], this.mapboxOptions.center[0]];
        }

        this.initializeMap();
    };

    DjangoMapboxPointFieldWidget.prototype.resetMap = function () {
        this.Super();
        if (this.addressAutoCompleteInput) {
            this.addressAutoCompleteInput.val('');
        }
        setMapboxId('');
    };

    DjangoMapboxPointFieldWidget.prototype.initializeMap = function () {
        if (this.map) {
            return;
        }
        this.map = new mapboxgl.Map(this.mapboxOptions);

        if (this.mapOptions.showZoomNavigation) {
            this.map.addControl(new mapboxgl.NavigationControl());
        }

        createV6Geocoder(this);
        $(this.mapElement).data('mwMapObj', this.map);
        $(this.mapElement).data('mwClassObj', this);

        if (!$.isEmptyObject(this.djangoGeoJSONValue)) {
            loadExistingGeolocation(this);
        }
    };

    DjangoMapboxPointFieldWidget.prototype.callPlaceTriggerHandler = function (lat, lng, place) {
        if (place === undefined) {
            reverseGeocodeV6(lng, lat, mapboxgl.accessToken).then(function (feature) {
                if (!feature) {
                    return;
                }
                if (this.addressAutoCompleteInput) {
                    this.addressAutoCompleteInput.val(featureLabel(feature));
                }
                setMapboxId(feature.properties.mapbox_id);
                $(document).trigger(
                    this.placeChangedTriggerNameSpace,
                    [feature, lat, lng, this.wrapElemSelector, this.locationInput]
                );
                if ($.isEmptyObject(this.locationFieldValue)) {
                    $(document).trigger(
                        this.markerCreateTriggerNameSpace,
                        [feature, lat, lng, this.wrapElemSelector, this.locationInput]
                    );
                } else {
                    $(document).trigger(
                        this.markerChangeTriggerNameSpace,
                        [feature, lat, lng, this.wrapElemSelector, this.locationInput]
                    );
                }
            }.bind(this));
        } else {
            const mapboxId = place.properties && place.properties.mapbox_id;
            if (mapboxId) {
                setMapboxId(mapboxId);
            }
            $(document).trigger(
                this.placeChangedTriggerNameSpace,
                [place, lat, lng, this.wrapElemSelector, this.locationInput]
            );
        }
    };

    }

    patchMapboxWidget();

})(mapWidgets.jQuery);
