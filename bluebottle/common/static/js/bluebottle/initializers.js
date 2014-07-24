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
        container.lookup('controller:currentUser');

        // Without the previous lookup the injection fails. We inject on the application object, rather than the container.
        // See: http://balinterdi.com/2014/05/01/dependency-injection-in-ember-dot-js.html
        application.inject("route", "tracker", "controller:tracker");

        application.inject("controller", "tracker", "controller:tracker");
        application.inject("controller:tracker", 'currentUser', "controller:currentUser");
    }
});
