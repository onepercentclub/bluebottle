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

    this.resource('passwordReset', {path: '/passwordreset/:reset_token'});

    this.resource('disableAccount', {path: '/disable/:user_id/:token'});

    this.resource('passwordRequest', {path: '/passwordrequest/:email'});
});

/*
 *  Routes
 */


App.UserIndexRoute = Em.Route.extend({
    beforeModel: function() {
        this.transitionTo('userProfile');
    }
});


App.UserProfileRoute = Em.Route.extend(App.ScrollToTop, App.AuthenticatedRouteMixin, {
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

App.UserSettingsRoute = Em.Route.extend(App.AuthenticatedRouteMixin, {
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

App.PasswordRequestRoute = Em.Route.extend({
    renderTemplate: function() {
        this.render('home');
        this.send('openInBox', 'passwordRequest');
    },

    model: function(params) {
        return Em.Object.create({email: params.email, failedToken: true})
    }
});

App.PasswordResetRoute = Em.Route.extend({
    renderTemplate: function() {
        this.render('home');
        this.send('openInBox', 'passwordReset');
    },

    model: function(params) {
        var record = App.PasswordReset.createRecord({
            id: params.reset_token
        });
        // Need this so that the adapter makes a PUT instead of POST
        record.transitionTo('loaded.saved');
        return record
    },

    beforeModel: function(transition) {

        return Ember.RSVP.Promise(function (resolve, reject) {
            var hash = {
                url: '/api/users/passwordset/' + transition.params.reset_token,
                type: 'get',
                contentType: 'application/json; charset=utf-8'
                };
            hash.success = function(response) {
                Ember.run(null, resolve, null)
            };
            hash.error = function(response) {
                Ember.run(null, reject, JSON.parse(response.responseText));
            };
            Ember.$.ajax(hash);

        })
    },
    actions: {
        error: function(error, transition) {
            transition.abort()
            this.transitionTo('passwordRequest', error.email)
        }
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
        return Em.Object.create({user_id: params.user_id, token: params.token});
    }
});
