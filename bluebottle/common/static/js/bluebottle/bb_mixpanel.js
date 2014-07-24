Ember.Application.initializer({
    name: 'registerTracker',
    before: 'injectTracker',

    initialize: function(container, application) {
        application.register("controller:tracker", App.TrackerController);
    }
});


Ember.Application.initializer({
    name: 'injectTracker',
    before: 'currentUser',

    initialize: function(container, application) {
        // Calling the lookup function seems to have the side-effect of instantiating the tracker controller.
        // Perhaps the call to lookup also registers the controller with the container so that it may be injected
        container.lookup('controller:tracker');

        // Without the previous lookup the injection fails. We inject on the application object, rather than the container.
        // See: http://balinterdi.com/2014/05/01/dependency-injection-in-ember-dot-js.html
        application.inject("route", "tracker", "controller:tracker");
        application.inject("controller", "tracker", "controller:tracker");


  }
});

/*
    Specialized controller for tracking (still coupled to Mixpanel at the moment)
 */
App.TrackerController = Em.ObjectController.extend({
   needs: "currentUser",

   init: function(){
       this._super();
       if (MIXPANEL_KEY && mixpanel) {
           this.set('_tracker', mixpanel);
       }


   }.observes('window'),

   trackEvent: function(name, properties) {
        if (Em.typeOf(properties) == 'undefined') properties = {};

        if (Em.typeOf(name) == 'string' && Em.typeOf(properties) == 'object') {
            this.get('_tracker').track(name, properties);
        }
    },

    setUserDetails: function(){
        if (this.get('controllers.currentUser.isAuthenticated')) {
            var user = this.get('controllers.currentUser');
            this.get('_tracker').register({
                "email": user.get('email'),
                "name": user.get('full_name')
            });
        }
    }.observes('controllers.currentUser.isAuthenticated')

});


