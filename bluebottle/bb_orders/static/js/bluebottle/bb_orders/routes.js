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
        var _this = this,
            status = _this.get('status');

        App.MyDonation.find({order: model.get('id')}).then(
            function(donations){
                // Take the first donation form the order and redirect to that project.
                var donation = donations.objectAt(0);

                // FIXME: For testing purposes we need to reload the project here.
                //        We also need to handle the donation on a fundraiser.
                donation.get('project').reload().then( function () {
                    _this.transitionTo('project', donation.get('project.id')).promise.then(function () {
                        // FIXME: Temporary for testing purposes
                        switch (status) {
                            case 'success':
                                _this.send('openInDynamic', 'donationSuccess', donation, 'modalFront');
                                break;

                            case 'pending':
                                _this.send('openInDynamic', 'donationPending', donation, 'modalFront');
                                // Display flash message until payment no longer 
                                // pending
                                _this.send('setFlash', gettext('Processing payment'), 'welcome', false);

                                // Check the status of the order and then clear 
                                // the flash message when the check resolves

                                // FIXME: Temporary for testing purposes we add
                                //        a timeout before checking order as the 
                                //        mock api will return a 'success' immediately
                                //        causing the toast to only show briefly.
                                setTimeout(function () {
                                    _this._checkOrderStatus(model).then(function () {
                                        _this.send('clearFlash');
                                    });
                                }, 2000);

                                break;

                            case 'cancelled':
                                // Create a new payment for this order
                                var payment = App.MyPayment.createRecord({order: model});

                                _this.send('openInDynamic', 'payment', payment, 'modalFront');
                                break;
                        }
                    });
                });
            },
            function(){
                throw new Em.error('Donation not found!');
            }
        );
    },

    _checkOrderStatus: function (order) {
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
