App.BbProjectMapComponent = Ember.Component.extend({
	mapStyle: [
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
	    }
    ],

    clusterOptions: {
        gridSize: 10,
        styles: [{
            url: "/static/assets/images/icons/marker_cluster.png",
            height: 23,
            width: 22,
            textColor: '#003580',
            anchorText: [-20, 0]
        }]
    },

    center: [52.3722499, 4.907800400000042],

    getCenter: function(){
        return new google.maps.LatLng(52.3722499, 4.907800400000042);
    }.property('center'),

    zoom_level:  3,

    map: null,

    markers: [],

    info_box_template: '<div class="maps-infobox"><div class="project-description-container"><figure class="project-thumbnail"><img src="{{image}}" alt="{{title}}" /></figure><p class="project-title">{{#link-to "project" this}}{{title}}{{/link-to}}</p><p class="project-meta"><span class="location"><span class="flaticon solid location-pin-1"></span> {{location}}</span><span class="tags"><span class="flaticon solid tag-2"></span> {{theme_name}}</span></p></div><a href="/#!/projects/{{id}}">LINK</a></div>',
    active_info_window: null,

	icon1: '/static/assets/images/icons/marker.png',
	icon2: '/static/assets/images/icons/marker_ok.png',

    initMap: function(){
        var view = this;
        this.geocoder = new google.maps.Geocoder();
        var view = this;
        var point = new google.maps.LatLng(22, 10);
        var MyMapType = new google.maps.StyledMapType(this.get("mapStyle"), {name: 'Grey'});

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
            minZoom: 2
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
        var comp = this,
            map = comp.get('map');
        var bounds = new google.maps.LatLngBounds();
        var markers = [];
        App.ProjectPreview.find({page_size: 500}).then(function(records){
            records.forEach(function(project){
                var marker = comp.placeMarker(project);
                markers.push(marker);
                bounds.extend(marker.position);
                //map.fitBounds(bounds);
            });
            var markerCluster = new MarkerClusterer(map, markers, comp.get('clusterOptions'));
        });

    },

    getProjectIcon: function(project){
        return project.get('status.id') == 4 ?  this.get('icon1'): this.get('icon2');
    },

    placeMarker: function(project){
        var view = this;

        // TODO: Use hbs template for popups.
        // var popupView = App.ProjectMapPopupView.create();
        // var template = Ember.Handlebars.compile('{{view App.ProjectMapPopupView}}');

        var template = Handlebars.compile(view.info_box_template);
        var title = project.get('title');
        if (title.length > 35) {
            title =  title.substring(0, 32) + '...';
        }
        var data = {
            'id': project.get('id'),
            'title': title,
            'description': project.get('description'),
            'image': project.get('image'),
            'location': project.get('country.name'),
			'theme_name': project.get('theme.name'),
			'pitch': project.get('pitch'),
            'slug': project.get('slug')
        }
        
        var html = template(data);

        var latLng = new google.maps.LatLng(project.get('latitude'), project.get('longitude'));

		var info_window = new InfoBox({
			content: html,
			disableAutoPan: false,
			maxWidth: 200,
			alignBottom: true,
			pixelOffset: new google.maps.Size(-200, -50),
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
		    icon: view.getProjectIcon(project)
	    });

	    google.maps.event.addListener(marker, 'click', function() {
            this.get("map").panTo(marker.getPosition());
            if (view.active_info_window) {
                view.active_info_window.close();
            }
            info_window.open(view.map, marker);
            view.active_info_window = info_window;
        });	
        
        return marker;
    },
    didInsertElement: function() {
        var view = this;
	    this.initMap();
        // To make sure
        this.get('markers').forEach(function(marker){
            marker.setMap(null);
            view.get('markers').removeObject(marker);
        });
        this.placeMarkers();
    }
});
