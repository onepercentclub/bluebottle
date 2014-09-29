/**
 *  Router Map
 */

App.Router.map(function(){
    // FIXME: Temporary for testing purposes
    this.resource('order', {path: '/orders/:order_id/:status'});
    // this.resource('order', {path: '/orders/:order_id'});
});

/**
 * Project Routes
 */
App.OrderRoute = Em.Route.extend({
    model: function(params) {
        // FIXME: Temporary for testing purposes
        this.set('status', params.status);

        return App.MyOrder.find(params.order_id);
    },

    redirect: function(model) {
        var _this = this;
        
        var donation = model.get('donations').objectAt(0);
            status = _this.get('status'),
            fundraiser = donation.get('fundraiser'),
            project = donation.get('project'),
            donationTarget = fundraiser ? fundraiser : project;

        _this.transitionTo(donationTarget.get('modelType'), donationTarget).promise.then(function () {
            // FIXME: Temporary for testing purposes
            switch (status) {
                case 'success':
                    if (donation.get('anonymous')){
                        _this.send('setFlash', gettext("Thank you for supporting this project"));
                    } else {
                        _this.send('openInDynamic', 'donationSuccess', donation, 'modalFront');
                    }
                    break;

                case 'pending':
                    // Display flash message until payment no longer pending
                    _this.send('setFlash', gettext('Processing payment'), 'is-loading', false);

                    // Check the status of the order and then clear 
                    // the flash message when the check resolves

                    // FIXME: Temporary for testing purposes we add
                    //        a timeout before checking order as the 
                    //        mock api will return a 'success' immediately
                    //        causing the toast to only show briefly.
                    setTimeout(function () {
                        _this._checkOrderStatus(model).then(function () {
                            _this.send('clearFlash');
                            _this.send('openInDynamic', 'donationSuccess', donation, 'modalFront');
                        });
                    }, 2000);

                    break;

                case 'cancelled':
                    // Create a new payment for this order
                    // TODO: set error message
                    App.MyOrderPayment.createRecord({order: model}).then(function (payment) {
                        _this.send('openInDynamic', 'orderPayment', payment, 'modalFront');
                    });

                    break;

                case 'error':
                    App.MyOrderPayment.createRecord({order: model, 'errors': {'detail': gettext('Oops, something went wrong. Please try again.')}}).then(function (payment) {
                        _this.send('openInDynamic', 'orderPayment', payment, 'modalFront');
                    });
                    break;
                             
                case 'failed':
                    // Create a new payment for this order
                    // TODO: set error message
                    var payment = App.MyOrderPayment.createRecord({order: model});
                    _this.send('openInDynamic', 'orderPayment', payment, 'modalFront');
                    break;
                default:
                    throw new Em.error('Incorrect order status: ' + status);
            }
        });
    },

    _checkOrderStatus: function (order) {
        // TODO: This is very dependend on payment service and payment types.
        // Maybe we can move the Order to 'success' earlier when Payment still has status 'pending'?
        return Ember.RSVP.Promise(function (resolve, reject) {
            // Check the status every 2.5 secs. This check is indefinite unless
            // the reloaded order changes status from pending.
            var checkInterval = setInterval(function () {
                checkStatus();
            }, 2500);

            var checkStatus = function () {
                // reload the order to fetch the latest status. If the order 
                // is no longer pending then resolve the promise. If the 
                // reload fails then we also resolve the promise.
                order.reload().then(function(reloadedOrder) {
                    if (reloadedOrder.get('status') != 'pending') {
                        // Stop the status check and resolve promise
                        stopCheckStatus();
                        Ember.run(null, resolve, reloadedOrder);
                    }
                }, function (reloadedOrder) {
                    // Stop the status check and resolve promise
                    stopCheckStatus();
                    Ember.run(null, resolve, reloadedOrder);
                });
            };

            var stopCheckStatus = function () {
                clearInterval(checkInterval);
            };
        });
    }
});
