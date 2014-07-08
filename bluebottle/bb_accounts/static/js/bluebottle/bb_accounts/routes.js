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

//    this.route('userActivate', {path: '/activate/:activation_key'});
    this.resource('passwordReset', {path: '/passwordreset/:reset_token'});

    this.resource('disableAccount', {path: '/disable/:user_id/:token'});
});

/*
 *  Routes
 */
App.SignupRoute = Em.Route.extend(App.ScrollToTop, {
    redirect: function() {
        var applicationController = this.controllerFor('application');

        if (applicationController.get('currentUser.isAuthenticated')) {
            this.transitionTo('home');
        }
    },

    model: function() {
        // FIXME We need to set the first and last name to an empty string or we'll get a 500 error.
        // FIXME This is a workaround for a bug in DRF2.
        return App.UserCreate.createRecord({
            first_name: '',
            last_name: '',
        });
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

    actions: {
        viewRecurringOrder: function() {
            var controller = this.controllerFor('currentOrder');
            controller.set('donationType', 'monthly');
            this.transitionTo('currentOrder.donationList')
        }
    }
});

App.PasswordResetRoute = Em.Route.extend({
    renderTemplate: function() {
        this.render('home');
        this.send('openInBox', 'passwordReset');
    },

    model: function(params) {
        var route = this;

        var record = App.PasswordReset.createRecord({
            id: params.reset_token
        });

        // Need this so that the adapter makes a PUT instead of POST
        record.transitionTo('loaded.saved');

        return record;
    }
});

App.DisableAccountRoute = Em.Route.extend({
    init: function(){
        this._super();
    },

   renderTemplate: function() {
       this.render('home');
       this.send('openInBox', 'disableAccount');
   },

    model: function(params){
        var route = this;
        var record = Em.Object.create({user_id: params.user_id, token: params.token});
        return record;
    }
});
