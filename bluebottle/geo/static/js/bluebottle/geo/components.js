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
    info_box_template: '<div class="maps-infobox"><h2 class="project-title">{{title}}</h2><p class="project-location"><em>{{location}}</em></p><img class="project-thumbnail" src="{{image}}" alt="{{title}}" /><p class="project-description">{{description}}</p></div>',
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
        console.log(this.get('projects').toString());
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
				pixelOffset: new google.maps.Size(0, -22),
				zIndex: null,
				boxClass: "info-windows",
				closeBoxURL: "",
				pane: "floatPane",
				enableEventPropagation: false,
				infoBoxClearance: "10px",
				position: latLng
			});
//        var info_window = new google.maps.InfoWindow({
//    		content: html
//	    });
        var marker = new google.maps.Marker({
		    position: latLng,
		    map: view.map,
		    title: project.get('title'),
		    icon: "/static/assets/images/icons/marker.png"
	    });

	    google.maps.event.addListener(marker, 'click', function() {
            if (view.active_info_window) {
                view.active_info_window.close();
            }
            info_window.open(view.map, marker);
            view.active_info_window = info_window;
        });
    },
    didInsertElement: function() {
	    this.initMap();

        this.placeMarkers();
    }
});
