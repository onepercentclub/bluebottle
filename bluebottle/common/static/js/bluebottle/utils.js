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

            record.save();
        },

        goToNextStep: function(){
            $("html, body").animate({ scrollTop: 0 }, 600);
            this.transitionToRoute(this.get('nextStep'));
        },

        updateRecordOnServer: function(){
            var controller = this;
            var model = this.get('model');

            model.one('becameInvalid', function(record) {
                controller.set('saving', false);
                model.set('errors', record.get('errors'));
            });

            model.one('didUpdate', function(){
                if (controller.get('nextStep')) {
                    $("html, body").animate({ scrollTop: 0 }, 600);
                    controller.transitionToRoute(controller.get('nextStep'));
                }
            });

            model.one('didCreate', function(){
                if (controller.get('nextStep')) {
                    $("html, body").animate({ scrollTop: 0 }, 600);
                    controller.transitionToRoute(controller.get('nextStep'));
                }
            });

            model.save();
        }

    },

    stopEditing: function() {
        var self = this;
        var record = this.get('model');
        var transaction = record.get('transaction');

        if (record.get('isDirty')) {
            Bootstrap.ModalPane.popup({
                classNames: ['modal'],
                heading: gettext('Save changed data?'),
                message: gettext('You have some unsaved changes. Do you want to save before you leave?'),
                primary: gettext('Save'),
                secondary: gettext('Cancel'),
                callback: function(opts, e) {
                    e.preventDefault();

                    if (opts.primary) {
                        record.save();
                    }

                    if (opts.secondary) {
                        record.rollback();
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


App.UploadFile= Ember.TextField.extend({
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
            var preview = "<img src='" + e.target.result + "' />";
            view.$().parents('form').find('.preview').remove();
            view.$().parent().after('<div class="preview">' + preview + '</div>');
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


// See/Use App.DatePicker
App.DatePickerValue = Ember.TextField.extend({
    type: 'hidden',
    valueBinding: "parentView.value"
});

// See/Use App.DatePicker
App.DatePickerWidget = Ember.TextField.extend({

    dateBinding: "parentView.value",
    configBinding: "parentView.config",

    didInsertElement: function(){
        var config = this.get('config');
        this.$().datepicker(config);
        this.$().datepicker('setDate', this.get('date'));
    },

    change: function(){
        this.set('date', this.$().datepicker('getDate'));
    }
});

// This renders a TextField with the localized date.
// On click it will use jQuery UI date picker dialog so the user can select a date.
// valueBinding should bind to a  DS.attr('date') property of an Ember model.
App.DatePicker = Ember.ContainerView.extend({
    config: {changeMonth: true, changeYear: true, yearRange: "c-100:c+10"},
    childViews: [App.DatePickerValue, App.DatePickerWidget]
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

    lookUpLocation: function() {
        var address = this.get('lookup');
        var view = this;
        view.geocoder.geocode( {'address': address}, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                view.placeMarker(results[0].geometry.location);
                view.set('latitude',  '' + results[0].geometry.location.lat().toString());
                view.set('longitude', '' + results[0].geometry.location.lng().toString());

            } else {
                alert('Geocode was not successful for the following reason: ' + status);
            }
        });
    },
    placeMarker: function (position) {
        var view = this;
        if (view.marker) {
            view.marker.setMap(null)
        }

        view.marker = new google.maps.Marker({
            position: position,
            map: view.map
        });
        view.map.panTo(position);
    },

    didInsertElement: function(){
        var view = this;
        this.geocoder = new google.maps.Geocoder();
        var view = this;
        var point = new google.maps.LatLng(view.get('latitude'), view.get('longitude'));
        var mapOptions = {
            zoom: 6,
            center: point,
            mapTypeId: google.maps.MapTypeId.ROADMAP
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

