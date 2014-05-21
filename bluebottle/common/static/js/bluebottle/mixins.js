/*
  Add mixin to routes which require authentication
 */

App.AuthenticatedRouteMixin = Ember.Mixin.create({
    beforeModel: function(transition) {
        var applicationController = this.controllerFor('application');
        
        // If not logged in then display the login popup for the user.
        if (!this.controllerFor('currentUser').get('isAuthenticated')) {
            // The popup box method is on the application route
            // TODO: is there a more elegant way to call the function from here?
            var self = this;

            self.transitionTo('signup');

            // Abort the transition as the login controller will handle the redirect after a successful login.
            // We only need to handle the case when the user clicks the close link on the login popup - this
            // is done below in a callback to the openInBox. 
            // transition.abort();

            // App.__container__.lookup("route:application").openInBox('login', null, null, function (options, event) {
            //     // If the user closed the login popup and there was no last url then transition to the home page
            //     var lastUrl = App.__container__.lookup('router:main').location.lastSetURL;
            //     if (!lastUrl && options.close) {
            //         self.transitionTo('home');
            //     }
            // });
        }
    }
});

/*
 Route mixin which will abort transition if the model save fails

 Note: Use route with a controller which has the App.ControllerObjectStatusMixin,
 or add modelStatus property to the controllers model.
 */
 
App.SaveOnTransitionRouteMixin = Ember.Mixin.create({
    skipExitSignal: true,
    _transitioning: false,

    deactivate: function() { 
      this._transitioning = false; 
    },

    actions: {
        willTransition: function(transition) {
            var self = this,
                controller = self.get('controller');
              
            // Don't try to save data if:
            // 1) it isn't dirty
            // 2) the route has skipExitSignal set to true
            // 3) a transition is already in progress
            if (controller.get('modelStatus') != 'dirty') { return true; }
            if (this.skipExitSignal) { return true; }
            if (this._transitioning) { return true; }

            // Create a promise => if successfully then retry transition
            this._transitioning = true;
            transition.abort();
            
            // Try to save the controllers data and retry transition if save successful
            controller.saveData().then(function (response) {
                transition.retry();
            }, null);

            return true;
        }
    }
 });

/*
 Mixin that controllers with editable models can use. E.g. App.UserProfileController

 @see App.UserProfileRoute and App.UserProfileController to see it in action.
 */
App.SaveOnExitMixin = Ember.Mixin.create({
    saveData: function() {
        var self = this;

        return new Ember.RSVP.Promise(function(resolve, reject) {
            $("body").animate({ scrollTop: 0 }, 600);

            var model = self.get('model'),
                controller = self;

            if (!model.get('isDirty')) {
                resolve(gettext('Model is not dirty.'));
                return;
            }

            // If there is a flash property on the controller then 
            // reset as we are changing steps now
            if (self.get('flash'))
                self.set('flash', null);

            // The class using this mixin must have an implementation of _save()
            // or use a mixin which includes one, eg App.ControllerObjectSaveMixin
            if (typeof self._save === 'function') {
                self._save().then(function () {
                    resolve(gettext('Model saved successfully.'));
                }, function () {
                    reject(gettext('Model could not be saved.'));
                });
            } else {
                resolve(gettext('Instance does not implement `_save`.'));
            }
        });
    },

    actions: {
        goToNextStep: function(){
            if (this.get('nextStep')){
                this.transitionToRoute(this.get('nextStep'));
            }
        },

        goToPreviousStep: function(){
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

    // TODO:  this should be an action / property on the Application Router so that 
    //        it can be reseting can be handled there by default and then other parts
    //        of the code can use it too.
    _setFlash: function (type, text) {
        this.set('flash', {
            type: type,
            text: text
        });
    },

    _save: function () {
        var self = this;

        return new Ember.RSVP.Promise(function(resolve, reject) {
            var model = self.get('model'),
                saveEvent = model.get('isNew') ? 'didCreate' : 'didUpdate',
                timer;        

            if (self.get('flash'))
                self.set('flash', null);

            model.one(saveEvent, function() {
                var message = gettext('Successfully saved.');
                self._setFlash('success', message);
                clearTimeout(timer);
                resolve(message);
            });

            model.one('becameInvalid', function () {
                clearTimeout(timer);
                reject(gettext('Model is invalid.'));
            });

            model.one('didError', function () {
                clearTimeout(timer);
                reject(gettext('Error saving model.'));
            });

            if (model) {
                model.set('errors', {});
                model.save();
            }

            // TODO: ugly hack until we start using Ember Data 1.0+ with it's
            //       save/find... thenable niceties
            timer = setTimeout( function () {
                // should never get here - didCreate, becameInvalid etc events should be triggered.
                reject(gettext('Hey! What are you doing here? Saving model failed.'));
            }, 10 * 1000);
        });
    },

    actions: {
        // TODO: can we remove this action? 
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
            imageUrl += "&key=" + MAPS_API_KEY;

        return imageUrl;
    }.property('latitude', 'longitude')
})
