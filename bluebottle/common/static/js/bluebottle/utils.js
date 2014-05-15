App.TimeNeededList = [
    {value: 0.25, title: gettext("15 minutes")},
    {value: 0.5, title: gettext("half an hour")},
    {value: 1, title: gettext("up to one hour")},
    {value: 2, title: gettext("two hours")},
    {value: 4, title: gettext("half a day")},
    {value: 8, title: gettext("one day")},
    {value: 16, title: gettext("two days")},
    {value: 40, title: gettext("one week")},
    {value: 80, title: gettext("two weeks")},
    {value: 160, title: gettext("one month")}

];

App.TimeNeededSelectView = Em.Select.extend({
    content: App.TimeNeededList,
    optionValuePath: "content.value",
    optionLabelPath: "content.title"
});


App.IsAuthorMixin = Em.Mixin.create({
    isAuthor: function () {
        var username = this.get('controllers.currentUser.username');
        var authorname = this.get('author.username');
        if (username) {
            return (username == authorname);
        }
        return false;
    }.property('author.username', 'controllers.currentUser.username')
});


/*
  Mixin for validating multiple properties in a model instance at runtime
*/
App.ModelValidationMixin = Ember.Mixin.create({
    ////
    // name: property to query for validation
    // fields: an array of properties which will be checked
    //
    validatedFieldsProperty: function(name, fields) {

        if (!fields || typeof fields['forEach'] !== 'function') throw new Error('Expected an array of fields to validate');

        var self = this;
        var checkFunc = function() {
            var valid = true;

            fields.forEach(function (field) {
                if (!self.get(field))
                    valid = false;
            });
            return valid;
        };

        var computedProp = Ember.ComputedProperty.property.apply(checkFunc, fields);
        Ember.defineProperty(self, name, computedProp);

    },
    missingFieldsProperty: function(name, fields) {
        if (!fields || typeof fields['forEach'] !== 'function') throw new Error('Expected an array of fields to validate');

        var self = this;
        var checkFunc = function() {
            var missing = Em.A(),
                friendlyNames = self.get('friendlyFieldNames');

            fields.forEach(function (field) {
                var fieldName;

                if (!self.get(field)) {
                    if (friendlyNames && friendlyNames[field]) {
                        fieldName = friendlyNames[field];
                    } else {
                        fieldName = field;
                    }

                    missing.addObject(fieldName);
                }
            });
            return missing;
        };

        var computedProp = Ember.ComputedProperty.property.apply(checkFunc, fields);
        Ember.defineProperty(self, name, computedProp);

    }

});


/*
 Mixin that controllers with editable models can use. E.g. App.UserProfileController

 @see App.UserProfileRoute and App.UserProfileController to see it in action.
 */
App.Editable = Ember.Mixin.create({
    saved: false,

    actions : {
        save: function(record) {
            var controller = this;

            if (record.get('isDirty')) {
                this.set('saving', true);
                this.set('saved', false);
            }

            record.one('didUpdate', function() {
                // record was saved
                controller.set('saving', false);
                controller.set('saved', true);
            });

            record.one('becameInvalid', function(record) {
                controller.set('saving', false);
            });

            record.save();
        },

        goToNextStep: function(){
            $("html, body").animate({ scrollTop: 0 }, 600);
            if (this.get('nextStep')) {
                this.transitionToRoute(this.get('nextStep'));
            } else {
                if (window.console){
                    console.log("Don't know were to go next");
                }
            }
        },

        updateRecordOnServer: function(){
            var controller = this;
            var model = this.get('model');

            model.one('becameInvalid', function(record) {
                controller.set('saving', false);
                model.set('errors', record.get('errors'));
                // Ember-data currently has no clear way of dealing with the state
                // loaded.created.invalid on server side validation, so we transition
                // to the uncommitted state to allow resubmission
                model.transitionTo('loaded.created.uncommitted');
            });

            if  (model.get('isNew')) {
                model.one('didCreate', function(){
                    controller.send('goToNextStep');
                });
            } else {
                model.one('didUpdate', function(){
                    controller.send('goToNextStep');
                });
            }


            model.save();
        }

    },

    stopEditing: function() {
        var self = this;
        var model = this.get('model');

        if (model.get('isDirty')) {
            Bootstrap.ModalPane.popup({
                classNames: ['modal'],
                heading: gettext('Save changed data?'),
                message: gettext('You have some unsaved changes. Do you want to save before you leave?'),
                primary: gettext('Save'),
                secondary: gettext('Cancel'),
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        model.save();
                    }
                    if (opts.secondary) {
                        model.rollback();
                    }
                }
            });
        }
    },

    saveButtonText: (function() {
        if (this.get('saving')) {
            return gettext('Saving');
        }
        return gettext('Save');
    }).property('saving')
});


App.UploadFile = Ember.TextField.extend({
    attributeBindings: ['name', 'accept'],
    type: 'file',

    didInsertElement: function(){
        // Or maybe try: https://github.com/francois2metz/html5-formdata.
        var view = this.$();
        if (Em.isNone(FileReader)) {
            $.getScript('//ajax.googleapis.com/ajax/libs/swfobject/2.2/swfobject.js').done(
                function(){
                    $.getScript('/static/assets/js/polyfills/FileReader/jquery.FileReader.min.js').done(
                        function(){
                            view.fileReader({filereader: '/static/assets/js/polyfills/FileReader/filereader.swf'});
                        }
                    );
                }
            );
        }
    },

    change: function (evt) {
        var files = evt.target.files;
        var reader = new FileReader();
        var file = files[0];
        var view = this;

        reader.onload = function(e) {
            var preview = "<figure><img src='" + e.target.result + "' /></figure>";
            // view.$().parents('form').find('.preview').remove();
            view.$().parents('.image-upload').find('figure').remove();
            // view.$().parent().after('<div class="preview">' + preview + '</div>');
            view.$().closest(".image-upload").find(".image-upload-drag").prepend(preview);
        };
        reader.readAsDataURL(file);
        var model = this.get('parentView.controller.model');
        this.set('file', file);
    }
});


App.UploadMultipleFiles = Ember.TextField.extend({
    type: 'file',
    attributeBindings: ['name', 'accept', 'multiple'],

    didInsertElement: function(){
        // Or maybe try: https://github.com/francois2metz/html5-formdata.
        var view = this.$();
        if (Em.isNone(File)) {
            $.getScript('//ajax.googleapis.com/ajax/libs/swfobject/2.2/swfobject.js').done(
                function(){
                    $.getScript('/static/assets/js/polyfills/FileReader/jquery.FileReader.min.js').done(
                        function(){
                            view.fileReader({filereader: '/static/assets/js/polyfills/FileReader/filereader.swf'});
                        }
                    );
                }
            );
        }
    },

    contentBinding: 'parentView.controller.content',

    change: function(e) {
        var controller = this.get('parentView.controller');
        var files = e.target.files;
        for (var i = 0; i < files.length; i++) {
            var reader = new FileReader();
            var file = files[i];
            reader.readAsDataURL(file);

            // Replace src of the preview..
            var view = this;
            view.$().parents('form').find('.preview').attr('src', '/static/assets/images/loading.gif');
            reader.onload = function(e) {
                view.$().parents('form').find('.preview').attr('src', e.target.result);
            }
            controller.addFile(file);
        }
    }
});

App.UploadedImageView = App.UploadFile.extend({
    attributeBindings: ['name', 'accept'],
    type: 'file',

    change: function (evt) {
        var files = evt.target.files;
        var reader = new FileReader();
        var file = files[0];
        var view = this;

        reader.onload = function(e) {
            var preview = "<img src='" + e.target.result + "' />";
			view.$().parents('.l-wrapper').find('.previewUpload').after('<div class="test">' + preview + '</div>');
        };
        reader.readAsDataURL(file);
        var model = this.get('parentView.controller.model');
        this.set('file', file);
    }
});


App.PopOverMixin = Em.Mixin.create({
   didInsertElement: function(){
        this.$('.has-popover').popover({trigger: 'hover', placement: 'left'});
        this.$('.has-tooltip').tooltip({trigger: 'hover', placement: 'right'});
   }
});


App.MapPicker = Em.View.extend({

	templateName: 'map_picker',
	marker: null,

	submit: function(e){
		e.preventDefault();
		this.lookUpLocation();
	},
	actions: {
		lookUpLocation: function() {
			var address = this.get('lookup');
			var view = this;

			view.geocoder.geocode( {'address': address}, function(results, status) {
				if (status == google.maps.GeocoderStatus.OK) {
					view.placeMarker(results[0].geometry.location);
					view.set('latitude',  '' + results[0].geometry.location.lat().toString());
					view.set('longitude', '' + results[0].geometry.location.lng().toString());

					var latlng = new google.maps.LatLng(view.get('latitude'), view.get('longitude'));
					view.geocoder.geocode({'latLng': latlng}, function(results, status) {
						if (status == google.maps.GeocoderStatus.OK) {
							for (var i = 0; i < results[0].address_components.length; i++) {
								if (results[0].address_components[i].types[0] == "country") {
									var code = results[0].address_components[i].short_name,
									    country = App.Country.find().filterProperty('code', code)[0];

									if (country)
										view.get('model').set('country', country);
								}
							}
						}

					});
				} else {
					alert('Geocode was not successful for the following reason: ' + status);
				}
			});
		}
	},
     placeMarker: function (position) {
         var view = this;
         if (view.marker) {
             view.marker.setMap(null)
         }

         view.marker = new google.maps.Marker({
             draggable: true,
             position: position,
             map: view.map
         });
         google.maps.event.addListener(view.marker, 'dragend', function(){
              var pos = view.marker.getPosition();
              view.set('latitude', pos.lat().toString());
              view.set('longitude', pos.lng().toString());
         });

         view.map.panTo(position);
     },

     didInsertElement: function(){
         var view = this;
         this.geocoder = new google.maps.Geocoder();
         var view = this;
         var point = new google.maps.LatLng(52.3747157,4.8986167);
         var latitude = view.get('latitude');
         var longitude = view.get('longitude');
         if (latitude && longitude){
             point = new google.maps.LatLng(latitude, longitude);
         }
         var mapOptions = {
             zoom: 2,
             center: point,
             mapTypeId: google.maps.MapTypeId.ROADMAP,
             mapTypeControlOptions: {
                 style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
                 position: google.maps.ControlPosition.BOTTOM_RIGHT
             }
         };
         view.map = new google.maps.Map(this.$('.map-picker').get(0), mapOptions);

         view.placeMarker(point);

         google.maps.event.addListener(view.map, 'click', function(e) {
             var loc = {};
             view.set('latitude', e.latLng.lat().toString());
             view.set('longitude', e.latLng.lng().toString());
             view.placeMarker(e.latLng);
         });
     }

});

App.FlashView = Em.View.extend();
