from django import forms
from mapwidgets.settings import mw_settings
from mapwidgets.widgets import MapboxPointFieldWidget


class CustomMapboxPointFieldWidget(MapboxPointFieldWidget):

    @property
    def media(self):
        return self._media(
            extra_js=[
                "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js",
                "/static/assets/admin/js/mapbox-sdk.min.js",
                "https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v4.7.2/mapbox-gl-geocoder.min.js",
            ],
            extra_css=[
                "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css",
                "https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v4.7.2/mapbox-gl-geocoder.css",
            ],
        )


class GeolocationMapboxPointFieldWidget(MapboxPointFieldWidget):

    @property
    def media(self):
        minified = not mw_settings.is_dev_mode
        css_paths = self.get_css_paths(
            [
                "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css",
            ],
            minified=minified,
        )
        base_js = list(
            self.settings.media.js.minified if minified else self.settings.media.js.dev
        )
        js_paths = [
            "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js",
        ] + base_js + [
            "admin/js/geolocation-map-widget.js",
        ]
        return forms.Media(css={"all": css_paths}, js=js_paths)
