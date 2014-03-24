/*
 Mixin that controllers with editable models can use. E.g. App.UserProfileController

 @see App.UserProfileRoute and App.UserProfileController to see it in action.
 */
App.SaveOnExitMixin = Ember.Mixin.create({

    actions : {
        goToStep: function(step){
            $("body").animate({ scrollTop: 0 }, 600);
            var model = this.get('model');
            var controller = this;

            if (!model.get('isDirty')) {
                if (step) controller.transitionToRoute(step);
            }

            model.one('becameInvalid', function(record) {
                // Ember-data currently has no clear way of dealing with the state
                // loaded.created.invalid on server side validation, so we transition
                // to the uncommitted state to allow resubmission
                if (record.get('isNew')) {
                    record.transitionTo('loaded.created.uncommitted');
                } else {
                    record.transitionTo('loaded.updated.uncommitted');
                }
            });

            if (model.get('isNew')) {
                model.one('didCreate', function(){
                    if (step) controller.transitionToRoute(step);

                });
            } else {
                model.one('didUpdate', function(){
                    if (step) controller.transitionToRoute(step);
                });
            }
            
            if (this.get('flash')) {
                this.set('flash', null);
            }

            model.set('errors', {});
            model.save();
        },

        goToPreviousStep: function(){
            var step = this.get('previousStep');
            this.send('goToStep', step);
        },

        goToNextStep: function(){
            var step = this.get('nextStep');
            this.send('goToStep', step);
        },

        goToNextNoSave: function(){
            if (this.get('nextStep')){
                this.transitionToRoute(this.get('nextStep'));
            }
        },

        goToPreviousNoSave: function(){
            if (this.get('previousStep')){
                this.transitionToRoute(this.get('previousStep'));
            }
        }

    }
});

App.ControllerObjectStatusMixin = Em.Mixin.create({

    modelStatus: function () {
        if (!this.get('model.isSaving') && !this.get('model.isDirty')) {
            return 'ready';
        } else if (this.get('model.isSaving')) {
            return 'busy';
        } else if (this.get('model.isDirty')) {
            return 'dirty';
        }
    }.property('model.isSaving', 'model.isDirty'),
    
});

App.ControllerObjectSaveMixin = Em.Mixin.create({
    flash: null,
    scrollTopBeforeSave: true,

    // If there is a modelStatus property on the controller
    // then use to re-set the flash message on change
    // This shouldn't happen after the didUpdate call
    // below has set a flash message but will happen when 
    // editing the record => isDirty or the record is 
    // reloaded, eg changing tabs
    setFlash: function () {
        this.set('flash', null);
    }.observes('modelStatus'),

    actions: {
        save: function() {
            var self = this,
                model = this.get('model');
            
            if (this.scrollTopBeforeSave)
                $('body').animate({ scrollTop: 0 }, 600);

            model.one('didUpdate', function () {
                self.set('flash', {
                    type: 'success',
                    text: gettext('Successfully updated')
                });
            });

            if (model) {
                model.set('errors', {});
                model.save();
            }
        },

        rollback: function() {
            if (this.scrollTopBeforeSave)
                $("body").animate({ scrollTop: 0 }, 600);

            var model = this.get('model');
            if (model) model.rollback();
        }
    }
    
});

// A mixin for classes with a latitude and longitude property
App.StaticMapMixin = Em.Mixin.create({
    // return url for Google static map based on lat / lng and (optional) google api key
    staticMap: function() {
        var latlng = this.get('latitude') + ',' + this.get('longitude'),
            imageUrl = "http://maps.googleapis.com/maps/api/staticmap?" + latlng + "&zoom=8&size=600x300&maptype=roadmap" +
            "&markers=color:pink%7Clabel:P%7C" + latlng + "&sensor=false";

        if (MAPS_API_KEY)
            imageUrl += "?key=" + MAPS_API_KEY;

        return imageUrl;
    }.property('latitude', 'longitude')
})