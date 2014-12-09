/**
 *  Router Map
 */

App.Router.map(function(){
    this.resource('order', {path: '/orders/:order_id/:status'});
});

/**
 * Project Routes
 */
App.OrderRoute = Em.Route.extend({
    model: function(params) {
        this.set('status', params.status);
        return App.MyOrder.find(params.order_id);
    },

    // Orders can not be transitioned from a failed state to an active state so 
    // we need to call the function below if the order failed, errored or was
    // cancelled. This will create a new order and donation with the same values.
    _resetOrder: function(order) {
        var donation = order.get('donations.firstObject');

        // Return a promise so we can easily handle the success/failure
        // when calling this function.
        return new Ember.RSVP.Promise(function(resolve, reject){
            // Create / save a new MyOrder with the same values
            App.MyOrder.createRecord({
                country: order.get('country'),
                user: order.get('user'),
                fundraiser: order.get('fundraiser'),
                project: order.get('project')
            }).save().then(function (newOrder) {
                // Now create / save the donation and associate with this order
                // NOTE: we assume only one donation in per order.
                // TODO: add some checking here to ensure all the fields
                //       are valid before assigning to the new record.
                App.MyDonation.createRecord({
                    amount: donation.get('amount'),
                    project: donation.get('project'),
                    fundraiser: donation.get('fundraiser'),
                    user: donation.get('user'),
                    created: donation.get('created'),
                    anonymous: donation.get('anonymous'),
                    order: newOrder
                }).save().then(function (newDonation) {
                    // Successfully loaded new order and donation
                    resolve(newOrder);
                }, function (newDonation) {
                    // Failed to load new donation
                    reject(newDonation.errors);
                })
            }, function (newOrder) {
                // Failed to load new order
                reject(newOrder.errors);
            });
        });
    },

        // A failed or cancelled status is handled the same way so we
    // have a convenience function here to handle both.
    _handleFailedCancelled: function(order) {
        var _this = this;

        this._resetOrder(order).then(function (newOrder) {
            App.MyOrderPayment.createRecord({order: newOrder}).then(function (orderPayment) {
                _this.send('openInDynamic', 'orderPayment', orderPayment, 'modalFront');
            }, function (orderPayment) {
                // TODO: set error message
                throw new Ember.Error("Failed to create OrderPayment: " + orderPayment.errors);
            });
        }, function (errors) {
            // TODO: set error message
            throw new Ember.Error("Failed to create order: " + errors);
        });
    },

    _handleSuccess: function (donation) {
        this.send('clearFlash');
        
        // If the donation is anonymous or there is no current user
        // then only show the thank you toast.
        if (donation.get('anonymous') || !this.get('currentUser.isAuthenticated')) {
            this.send('closeModal');
            
            if (donation.get('fundraiser')) {
                flashMessage = gettext("Thank you for supporting this fundraiser");
            } else {
                flashMessage = gettext("Thank you for supporting this project");
            }
            this.send('setFlash', flashMessage);
        } else {
            // Call closeModal as one might be open. We need to 
            // wait for a defer to resolve so we are sure the modal has closed
            // before we try to open another one.
            // FIXME: This needs to be handled in bb_modal library, eg if the 
            //        action to open a new modal is called and one is already
            //        open then either close / re-open, or handle a transition.
            var defer = Ember.RSVP.defer(),
                _this = this;

            // Redirect to the order route.
            defer.promise.then(function() {
                _this.send('openInDynamic', 'donationSuccess', donation, 'modalFront');
            });

            this.send('closeModal', defer);
        }
    },

    redirect: function(model) {
        var _this = this,
            order = model,
            donation = order.get('donations.firstObject');
            status = order.get('status'),
            fundraiser = donation.get('fundraiser'),
            project = donation.get('project'),
            donationTarget = fundraiser ? fundraiser : project;

        _this.transitionTo(donationTarget.get('modelType'), donationTarget).promise.then(function () {
            switch (status) {
                case 'success':
                    _this._handleSuccess(donation);

                    break;

                case 'pending':
                    _this._handleSuccess(donation);

                    break;

                case 'failed':
                    _this._handleFailedCancelled(order);
                    break;

                case 'cancelled':
                    _this._handleFailedCancelled(order);
                    break;

                case 'error':
                    App.MyOrderPayment.find({order: order.get('id')}).then(function(orderPayment) {
                        _this._resetOrder(order).then(function (newOrder) {
                            // For payment errors we:
                            // 1) return an error message
                            // 2) set the same payment method
                            var error = {'detail': gettext('Oops, something went wrong. Please try again.')},
                                paymentMethod = orderPayment.get('firstObject.payment_method');

                            App.MyOrderPayment.createRecord({
                                order: newOrder, 
                                payment_method: paymentMethod, 
                                errors: error
                            }).then(function (orderPayment) {
                                _this.send('openInDynamic', 'orderPayment', orderPayment, 'modalFront');
                            }, function (orderPayment) {
                                // TODO: set error message
                                throw new Ember.Error("Failed to create OrderPayment: " + orderPayment.errors);
                            });
                        }, function (errors) {
                            // TODO: set error message
                            throw new Ember.Error("Failed to create order: " + errors);
                        });
                    });

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
