from django import forms
from mapwidgets.settings import mw_settings
from mapwidgets.widgets import MapboxPointFieldWidget


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


class CustomMapboxPointFieldWidget(GeolocationMapboxPointFieldWidget):
    pass
