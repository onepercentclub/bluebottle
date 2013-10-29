/**
 * Router Map
 */


App.Router.map(function() {

    this.resource('currentOrder', {path: '/support'}, function() {
        this.route('donationList', {path: '/donations'});
        this.route('voucherList', {path: '/giftcards'});
        this.resource('paymentProfile', {path: '/details'});
        this.resource('paymentSignup', {path: '/signup'});
        this.resource('paymentSelect', {path: '/payment'}, function() {
            this.route('paymentError', {path: '/error'});
        });
    });

    this.resource('orderThanks', {path: '/support/thanks/:order_id'});
    this.resource('recurringOrderThanks', {path: '/support/monthly/thanks'});

    this.resource('ticker', {path: '/latest-donations'});

});





/**
 * Current Order Routes
 */

// Redirect to the donations list if somebody tries load '/support'.
App.CurrentOrderIndexRoute = Em.Route.extend({
    redirect: function() {
        this.transitionTo('currentOrder.donationList');
    }
});


App.CurrentOrderRoute = Em.Route.extend({
    model: function(params) {
        return App.CurrentOrder.find('current');
    }
});


App.CurrentOrderDonationListRoute = Em.Route.extend({
    model: function(params) {
        return this.modelFor('currentOrder').get('donations');
    },

    setupController: function(controller, donations) {
        this._super(controller, donations);
        this.controllerFor('currentOrder').set('isVoucherOrder', false);

        // Set the monthly order.
        App.Order.find({status: 'recurring'}).then(function(recurringOrders) {
            if (recurringOrders.get('length') > 0) {
                controller.set('recurringOrder', recurringOrders.objectAt(0))
            } else {
                controller.set('recurringOrder', null)
            }
        });

        // Set the top three projects
        App.ProjectPreview.find({ordering: 'popularity', phase: 'campaign'}).then(function(projects) {
            controller.set('topThreeProjects', projects.slice(0, 3));
        });

        // set the recurring payment
        App.RecurringDirectDebitPayment.find({}).then(function(recurringPayments) {
            if (recurringPayments.get('length') > 0) {
                controller.set('recurringPayment', recurringPayments.objectAt(0));
            }else {
                controller.set('recurringPayment', null);
            }
        });
    }
});


App.CurrentOrderVoucherListRoute = Em.Route.extend({
    model: function(params) {
        var order = this.modelFor('currentOrder');
        return order.get('vouchers');
    },

    setupController: function(controller, vouchers) {
        this._super(controller, vouchers);
        this.controllerFor('currentOrder').set('isVoucherOrder', true);
    }
});


App.OrderThanksRoute = Em.Route.extend({
    model: function(params) {
        var route = this;
        var order = App.Order.find(params.order_id);
        order.one('becameError', function() {
            route.controllerFor('application').setProperties({
                display_message: true,
                isError: true,
                message_title: "",
                message_content: "Sorry, we can't find your order."
            });
            route.replaceWith('home');
        });
        return order;
    }
});


App.RecurringOrderThanksRoute = Em.Route.extend({
// FIXME: Enable this when we fix the issue with transitioning to this route without a full page reload.
//    beforeModel: function() {
//        if (!this.controllerFor('currentUser').get('isAuthenticated')) {
//            this.transitionTo('home');
//        }
//    },

    model: function(params) {
        return App.Order.find({status: 'recurring'}).then(function(orders) {
            if (orders.get('length') > 0) {
                return orders.objectAt(0);
            }
            this.transitionTo('home');
        });
    },

    setupController: function(controller, order) {
        this._super(controller, order);

        App.RecurringDirectDebitPayment.find({}).then(function(recurringPayments) {
            if (recurringPayments.get('length') > 0) {
                controller.set('recurringPayment', recurringPayments.objectAt(0));
            } else {
                controller.set('recurringPayment', null);
            }
        });

        // Set the top three projects
        App.ProjectPreview.find({ordering: 'popularity', phase: 'campaign'}).then(function(projects) {
            controller.set('topThreeProjects', projects.slice(0, 3));
        });
    }
});


/**
 * Payment for Current Order Routes
 */

App.PaymentProfileRoute = Em.Route.extend({
    beforeModel: function() {
        var order = this.modelFor('currentOrder');
        if (order.get('isVoucherOrder')) {
            if (order.get('vouchers.length') <= 0 ) {
                this.transitionTo('currentOrder.voucherList')
            }
        } else {
            var controller = this.controllerFor('currentOrderDonationList');
            if (controller.get('editingRecurringOrder')) {
                if (controller.get('recurringTotal') == 0 && this.get('recurringTotal') == controller.get('recurringOrder.total')) {
                    this.transitionTo('currentOrder.donationList')
                }
            } else {
                if (!order.get('recurring') && order.get('donations.length') <= 0 ) {
                    this.transitionTo('currentOrder.donationList')
                }
            }
        }

    },

    model: function(params) {
        return App.PaymentProfile.find('current');
    }
});


App.PaymentSignupRoute = Em.Route.extend({
    model: function(params) {
        var model = App.UserCreate.createRecord();
        return App.PaymentProfile.find('current').then(function(profile){
            model.set('email', profile.get('email'));
            model.set('first_name', profile.get('firstName'));
            model.set('last_name', profile.get('lastName'));
            return model;
        });
    }
});


App.PaymentSelectRoute = Em.Route.extend({
    beforeModel: function() {
        var order = this.modelFor('currentOrder');
        if (!order.get('paymentProfileComplete')) {
            this.replaceWith('paymentProfile');
        } else if (order.get('recurring')) {
            this.replaceWith('recurringDirectDebitPayment');
        }
    },

    model: function(params) {
        return App.Payment.find('current');
    }
});


App.PaymentSelectPaymentErrorRoute = Em.Route.extend({
    beforeModel: function() {
        this.controllerFor('currentOrder').setProperties({
            display_message: true,
            isError: true,
            autoHideMessage: false,
            message_content: 'There was an error with your payment. Please try again.'
        });

        var order = this.modelFor('currentOrder');
        if (order.get('isVoucherOrder')) {
            this.replaceWith('currentOrder.voucherList');
        } else {
            this.replaceWith('currentOrder.donationList');
        }
    }
});


App.RecurringDirectDebitPaymentRoute = Em.Route.extend({
    beforeModel: function() {
        var order = this.modelFor('currentOrder');
        if (!order.get('recurring')) {
            this.transitionTo('paymentSelect');
        }
    },

    model: function() {
        var route = this;
        return App.RecurringDirectDebitPayment.find({}).then(function(recordList) {
                var store = route.get('store');
                if (recordList.get('length') > 0) {
                    var record = recordList.objectAt(0);
                    return record;
                } else {
                    return store.createRecord(App.RecurringDirectDebitPayment);
                }
            }
        )
    }
});


// Show the latest donations
App.TickerRoute = Em.Route.extend({
    model: function(params) {
        return  App.Ticker.find();
    }
});