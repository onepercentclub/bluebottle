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
        var username = this.get('currentUser.username');
        var authorname = this.get('author.username');
        if (username) {
            return (username == authorname);
        }
        return false;
    }.property('author.username', 'currentUser.username')
});

// It Provides different validations
// standart empty fields validation (_requiredFieldsChecker and blockingErrors)
// validation based on fields errors (validateErrors, enabled by calling enableValidation)
// for examples (go to bb_accounts/controllers.js
App.ControllerValidationMixin = Ember.Mixin.create({

    fixedFieldsMessage: gettext('That\'s better'),

    // In your controller define fieldsToWatch (a list of fields you want to watch)
    // you will be able to use then: errorsFixed and blockSubmit
    // errorsFixed: true if there were errors which are now fixed
    errorsFixed: false,

    // blockErrors: true if there are still blocking errors which prevent to submit
    blockingErrors: true,

    // to prevent the error validation we set validationEnabled to false
    // set to true to enable it
    validationEnabled: false,

    // used in validateErrors function
    errorDictionaryFields: ['property', 'validateProperty', 'message', 'priority'],

    // set validationEnable to true, this has to be called from the controller to enable the validation
    // I use it since we want to be in control when to start the validation, for example just after
    // pressing a submit button
    enableValidation: function() {
        this.set('validationEnabled', true)
    },

    // set the strength of the field, use this in the template
    fieldStrength: function(field) {

        var specialChar = (/(?=.*[!@#$%^&*])/)
        var upperAndLowerChar = (/(?=.*[A-Z])(?=.*[a-z])/)
        var numberChar = (/(?=.*[0-9])/)

        // field not fulfilled
        if (!field){
            return ""
        }

        // less than 6 char long and at least lower and upper case to be fair
        if (field.length > 6 && field.search(upperAndLowerChar) == 0) {
            // at least a specialChar or a numberChar to be strong
            if ((field.search(specialChar) == 0) || (field.search(numberChar) == 0)) {
                return gettext("strong")
            }
            return gettext("fair")
        }
        return gettext("weak")
    },

    _apiErrors: function(errors) {
        // we just show one error at the time
        var firstError = Em.Object.create();
        var resultErrors = Em.Object.create(errors);
        for (var key in resultErrors){
            // capitalize the first letter of the key add the related error and set it to the first error
            // TODO: I add the key to the message since when a field is required the error message doesn't say which one.
            firstError.set('error', (key.charAt(0).toUpperCase() + key.slice(1)) + ": " +resultErrors[key])
            return firstError
        }
    },

    //[{
    // 'property': propertyValue,
    // 'validateProperty': validateProperty,
    // 'message': message,
    // 'priority': priorityNumber
    // },
    // ...,]
    _clientSideErrors: function(arrayOfDict, model) {
        // array check otherwise throw error
        if (!Em.isArray(arrayOfDict))
            throw new Error('Expected an array of fields to validate');

        var _this = this,
            currentValidationError = null,
            currentErrorPriority = null,
            errorList = {};

        // for each element of the array
        arrayOfDict.forEach(function (dict) {
            //validate if the dictionary has the right fields
            if(Em.compare(Object.keys(dict).sort(), _this.errorDictionaryFields.sort()) < 0)
                throw new Error('Expected a dictionary with correct keys');

            // evaluate the property, if it's not valid
            if (!model.get(dict.validateProperty)) {
                errorList[dict.property] = dict['message']
                // set the error only if the priority is higher than the current one
                // maybe check also for the same property name
                if (!currentErrorPriority || currentErrorPriority > dict.priority ) {
                    currentErrorPriority = dict.priority

                    // if there were no currentErrors
                    if (!currentValidationError)
                        currentValidationError = Em.Object.create();

                    currentValidationError.set('error', dict['message'])
                }
            }

        });

        this.set("errorList", errorList);
        this._allErrors(errorList);
        
        return currentValidationError
    },

    _allErrors: function(errorList) {
        var _this = this;
        var errors = Ember.makeArray(this.get('errorDefinitions'));

        var allFieldErrors = true;
        for (var i=0; i < errors.length;i++){
            if (!(errors[i].property in errorList)){
                allFieldErrors = false;
            }
        }
        this.set('allError', allFieldErrors);
    },

    validateErrors: function(arrayOfDict, model, ignoreApiErrors) {
        if (!this.get('validationEnabled'))
            return null

        // API errors
        if (!ignoreApiErrors && model.get('errors')){
            return this._apiErrors(model.get('errors'))
        }
        // client side validation
        return this._clientSideErrors(arrayOfDict, model)
    },

    // At runtime observers are attached to this function
    // it calls the validateAndCheck function
    _checkErrors: function() {
        // Check if there were previous errors which are now fixed
        if (this.get('validationErrors')) {
            if (this._validateAndCheck()) {
                this.set('errorsFixed', true)
            }else {
                this.set('errorsFixed', false)
            }
        }
    },

    // return true if there are no errors
    _validateAndCheck: function() {
        // run the validateErrors and set the errors in validationErrors
        this._validate()
        return !this.get('validationErrors')
    },

    // run the validateErrors and set the errors in validationErrors
    _validate: function() {
        this.set('validationErrors', this.validateErrors(this.get('errorDefinitions'), this.get('model'), true));
    },

    // set blockingErrors to true if there are fields which aren't fulfilled
    // at runtime observers are attached to this function
    _requiredFieldsChecker: function() {
        var _this = this
        _this.set('blockingErrors', false)
        _this.get('requiredFields').forEach(function(field){
            if (!_this.get(field)){
                _this.set('blockingErrors', true)
            }
        })
    },

    // Dynamically assign observerFields to a function f
    // [http://stackoverflow.com/questions/13186618/how-to-dynamically-add-observer-methods-to-an-ember-js-object]
    _dynamicObserverCreator: function (observerFields, f) {
        if (this.get(observerFields)) {
            // dynamically assign observer fields to _checkErrors function
            // [http://stackoverflow.com/questions/13186618/how-to-dynamically-add-observer-methods-to-an-ember-js-object]
            this.get(observerFields).forEach(function(field) {
                Ember.addObserver(this, field, this, f)
            }, this);
        }
    },
    // Remove the observers when the object is destroyed
    _dynamicObserverRemover: function(observerFields, f) {
        if (this.get(observerFields)){
            this.get(observerFields).forEach(function(field) {
                Ember.removeObserver(this, field, this, f);
            }, this);
        }
    },

    init: function () {
        this._super();

        // Dynamically assign observerFields to a function f
        this._dynamicObserverCreator('fieldsToWatch', '_checkErrors');
        this._dynamicObserverCreator('requiredFields', '_requiredFieldsChecker');
    },

    willDestroy: function() {
        this._super();

        // Remove the observers when the object is destroyed
        this._dynamicObserverRemover('fieldsToWatch', '_checkErrors')
        this._dynamicObserverRemover('requiredFields', '_requiredFieldsChecker')
    }
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

    keyPress: function (evt) {
        var code = evt.which;
        // If enter key pressed
        if (code == 13) {
            evt.preventDefault();
            this.send('lookUpLocation');
        }
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
