/**
 * Router mapping
 */
App.Router.map(function(){
	this.resource('signup');

    this.resource('user', {path: '/member'}, function() {
        this.resource('userProfile', {path: '/profile/'});
        this.resource('userSettings', {path: '/settings'});

        // TODO: isolate this
        this.resource('userOrders', {path: '/orders'});
    });
    this.resource('viewProfile', {path: '/member/profile/:user_id'});

    this.route('userActivate', {path: '/activate/:activation_key'});
    this.resource('passwordReset', {path: '/passwordreset/:reset_token'});
});

/*
 *  Routes
 */
App.SignupRoute = Em.Route.extend(App.ScrollToTop, {
    redirect: function() {
        if (this.controllerFor('currentUser').get('isAuthenticated')) {
            this.transitionTo('home');
        }
    },

    model: function() {
        var transaction = this.get('store').transaction();
        // FIXME We need to set the first and last name to an empty string or we'll get a 500 error.
        // FIXME This is a workaround for a bug in DRF2.
        return transaction.createRecord(App.UserCreate, {first_name: '', last_name: ''});
    }
});


App.UserIndexRoute = Em.Route.extend({
    beforeModel: function() {
        this.transitionTo('userProfile');
    }
});


App.UserProfileRoute = Em.Route.extend(App.ScrollToTop, {
    model: function() {
        var route = this;
        return App.CurrentUser.find('current').then(function(user) {
            return App.User.find(user.get('id_for_ember'));
        });
    },

    deactivate: function() {
        this.controllerFor('userProfile').stopEditing();
    }

});

App.ViewProfileRoute = Em.Route.extend({
    model: function(params) {
        var model = App.User.find(params.user_id);
        var route = this;
        model.on('becameError', function() {
            route.transitionTo('error.notFound');
        });
        return model;
    }
});

App.UserSettingsRoute = Em.Route.extend({

    model: function() {
        var route = this;

        return App.CurrentUser.find('current').then(function(user) {
            return App.UserSettings.find(user.get('id_for_ember'));
        });
    },

    deactivate: function() {
        this.controllerFor('userSettings').stopEditing();
    }
});

// TODO: separate this
App.UserOrdersRoute = Em.Route.extend({
    model: function(params) {
        return App.RecurringDirectDebitPayment.find({}).then(function(recurringPayments) {
            if (recurringPayments.get('length') > 0) {
                return recurringPayments.objectAt(0);
            }else {
                return null;
            }
        });
    },

    setupController: function(controller, recurringPayment) {
        if (!Em.isNone(recurringPayment)) {
            this._super(controller, recurringPayment);
            controller.startEditing();
        } else {
            // Ember doesn't let you add other things to the controller when a record hasn't been set.
            this._super(controller, App.RecurringDirectDebitPayment.createRecord({fakeRecord: true}));
        }

        // Set the monthly order.
        App.Order.find({status: 'recurring'}).then(function(recurringOrders) {
            if (recurringOrders.get('length') > 0) {
                controller.set('recurringOrder', recurringOrders.objectAt(0))
            } else {
                controller.set('recurringOrder', null)
            }
        });

        // Set the closed orders.
        App.Order.find({status: 'closed'}).then(function(closedOrders) {
            controller.set('closedOrders', closedOrders);
        });
    },

    deactivate: function() {
        this.controllerFor('userOrders').stopEditing();
    },

    events: {
        viewRecurringOrder: function() {
            var controller = this.controllerFor('currentOrder');
            controller.set('donationType', 'monthly');
            this.transitionTo('currentOrder.donationList')
        }
    }
});


App.UserActivateRoute = Em.Route.extend({

    model: function(params) {
        var currentUser = App.CurrentUser.find('current');
        return App.UserActivation.find(params.activation_key);
    },

    // FIXME: Find a better solution than the run.later construction.
    setupController: function(controller, activation) {

        var currentUser = App.CurrentUser.find('current');

        var route = this;
        currentUser.one('didReload', function() {
            // User profile needs to load it's own currentUser apparently so unload this here.
            currentUser.unloadRecord();
            route.transitionTo('userProfile');
        });

        // This seems the only way to (more or less) always load the logged in user,
        Em.run.later(function() {
            currentUser.transitionTo('loaded.saved');
            App.set('csrfToken', getCookie('csrftoken'));
            currentUser.reload();
        }, 3000);

        var messageTitle   = "Welcome";
        var messageContent = "Hurray! We're very happy that you joined 1%CLUB, welcome on board! You can start by filling in your profile.";

        this.controllerFor('application').setProperties({
            display_message: true,
            message_title: messageTitle,
            message_content: messageContent
        });
    },

    events: {
        error: function (reason, transition) {
            this.controllerFor('application').setProperties({
                display_message: true,
                isError: true,
                message_title: '',
                message_content: 'There was a problem activating your account. Please contact us for assistance.'
            });
            this.transitionTo('home');
        }
    }
});


App.PasswordResetRoute = Em.Route.extend({
    model: function(params) {
        var route = this;

        var record = App.PasswordReset.createRecord({
            id: params.reset_token
        });

        // Need this so that the adapter makes a PUT instead of POST
        record.transitionTo('loaded.saved');

        record.on('becameError', function() {
            route.controllerFor('application').setProperties({
                display_message: true,
                isError: true,
                message_title: '',
                message_content: gettext('The token you provided is expired. Please reset your password again.')
            });

            route.replaceWith('home');
        });
        return record;
    }
});
