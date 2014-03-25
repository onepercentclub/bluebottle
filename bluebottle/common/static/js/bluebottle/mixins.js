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

            if (model.get('isNew')) {
                model.one('didCreate', function(){
                    if (step) controller.transitionToRoute(step);
                });
            } else {
                model.one('didUpdate', function(){
                    if (step) controller.transitionToRoute(step);
                });
            }

            // If there is a flash property on the controller then 
            // reset as we are changing steps now
            if (this.get('flash') && step)
                this.set('flash', null);

            // The class using this mixin must have an implementation of _save()
            // or use a mixin which includes one, eg App.ControllerObjectSaveMixin
            if (typeof this._save === 'function')
              this._save();
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
    redirectRouteName: 'home',

    // If there is a modelStatus property on the controller
    // then use to re-set the flash message on change
    // This shouldn't happen after the didUpdate call
    // below has set a flash message but will happen when 
    // editing the record => isDirty or the record is 
    // reloaded, eg changing tabs
    resetFlash: function () {
        this.set('flash', null);
    }.observes('modelStatus'),

    _save: function () {
        var self = this,
            model = this.get('model');        

        if (this.get('flash'))
            this.set('flash', null);

        model.one('didUpdate', function () {
            self.set('flash', {
                type: 'success',
                text: gettext('Successfully saved')
            });
        });

        if (model) {
          model.set('errors', {});
          model.save();
        }
    },

    actions: {
        saveAndRedirect: function () {
            var model = this.get('model');
            
            // If the model isn't dirty then nothing to save so 
            // just fulfil the redirect
            if (!model.get('isDirty')) {
                this.transitionToRoute(this.redirectRouteName);
                return;
            }

            var self = this,
                redirected = false,
                saveEvent = model.get('isNew') ? 'didCreate' : 'didUpdate';

            var t = model.one(saveEvent, function () {
                if (!redirected) {
                    redirected = true;
                    self.transitionToRoute(self.redirectRouteName);
                }
            });

            // If the save was invalid then we should cancel the redirect
            // otherwise the model.one above will trigger later when/if the
            // model is successfully updated/created => causing a redirect
            // unless the redirected variable is true.
            // TODO: It would be better to get a 'handle' for the one off
            //       trigger above and then cancel it if the save was invalid
            model.one('becameInvalid', function () {
                redirected = true;
            });

            this._save();
        },

        save: function() {
            if (this.scrollTopBeforeSave)
                $('body').animate({ scrollTop: 0 }, 600);

            this._save();
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