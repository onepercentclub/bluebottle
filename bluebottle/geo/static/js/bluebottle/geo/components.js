var mapStyle = [
    {
        featureType: "administrative",
        elementType: "geometry",
        stylers: [
            { visibility: "off" },
        ]
    },  {
        elementType: "labels",
        stylers: [
            { visibility: "off" },
        ]
    },{
        featureType: "road",
        stylers: [
            { visibility: "off" }
        ]
    },{
        featureType: "poi",
        stylers: [
            { visibility: "off" }
        ]
    },{
        featureType: "landscape",
        elementType: "geometry.fill",
        stylers: [
            { color: "#AAAAAA" }
        ]
    },{
        featureType: "water",
        stylers: [
            { color: "#FFFFFF" },
        ]
    },{
    }
];

App.BbProjectMapComponent = Ember.Component.extend({

    projects: function(){
        return App.ProjectPreview.find();
    }.property(),
    center: [52.3722499, 4.907800400000042],
    getCenter: function(){
        return new google.maps.LatLng(52.3722499, 4.907800400000042);
    }.property('center'),
    zoom_level:  3,
    map: null,
	markers: [],
    info_box_template: '<div class="maps-infobox"><h2 class="project-title">{{title}}</h2><div class="project-description-container"><figure class="project-thumbnail"><img src="{{image}}" alt="{{title}}" /></figure><div class="project-description"><p>{{pitch}}</p><p><span class="location"><span class="flaticon solid location-pin-1"></span> Location</span><span class="tags"><span class="flaticon solid tag-2"></span> Tags</span></p></div></div>',
    active_info_window: null,

    initMap: function(){
        var view = this;
        this.geocoder = new google.maps.Geocoder();
        var view = this;
        var point = new google.maps.LatLng(22, 10);
        var MyMapType = new google.maps.StyledMapType(mapStyle, {name: 'Grey'});

        var mapOptions = {
            zoom: 2,
            center: point,
            scrollwheel: false,
            panControl: false,
            zoomControl: true,
            mapTypeControl: false,
            scaleControl: false,
            streetViewControl: false,
            overviewMapControl: false,
            disableAutoPan: true,
//            mapTypeControlOptions: {
//                mapTypeIds: [
//                    'bb',
//                    'terrain',
//                    'satellite'
//                ]
//            }
        };
        view.map = new google.maps.Map(view.$('.bb-project-map').get(0), mapOptions);
        view.map.mapTypes.set('bb', MyMapType);
        view.map.setMapTypeId('bb');
	    google.maps.event.addListener(view.map, 'click', function() {
            if (view.active_info_window) {
                view.active_info_window.close();
            }
        });
    },

    placeMarkers: function() {
        var comp = this;
        this.get('projects').forEach(function(project){
            comp.placeMarker(project);
        });
    },

    placeMarker: function(project){
        var view = this;
        var template = Handlebars.compile(view.info_box_template);
        var data = {
            'title': project.get('title'),
            'description': project.get('description'),
            'image': project.get('image'),
            'location': project.get('country.name'),
        }
		
        var html = template(data);
        var latLng = new google.maps.LatLng(project.get('latitude'), project.get('longitude'));

		var info_window = new InfoBox({
			content: html,
			disableAutoPan: false,
			maxWidth: 200,
			alignBottom: true,
			pixelOffset: new google.maps.Size(-200, -30),
			zIndex: null,
			boxClass: "info-windows",
			closeBoxURL: "",
			pane: "floatPane",
			enableEventPropagation: false,
			infoBoxClearance: "10px",
			position: latLng
		});

        var marker = new google.maps.Marker({
		    position: latLng,
		    map: view.map,
		    title: project.get('title'),
		    icon: "/static/assets/images/icons/map-location.png"
	    });
		
	    google.maps.event.addListener(marker, 'click', function() {
			view.markers.forEach(function(m) {
				m.setIcon("/static/assets/images/icons/map-location.png");
			});
		    this.setIcon("/static/assets/images/icons/map-location-active.png");
            if (view.active_info_window) {
                view.active_info_window.close();
            }
            info_window.open(view.map, marker);
            view.active_info_window = info_window;
        });	


		view.markers.push(marker);
    },
    didInsertElement: function() {
	    this.initMap();

        this.placeMarkers();
    }
});
