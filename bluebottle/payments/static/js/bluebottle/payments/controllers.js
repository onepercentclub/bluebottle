App.PaymentController = Em.ObjectController.extend({
    willOpen: function () {
        var _this = this,
            controller = this.get('controller'),
            payment = this.get('model');

        // TODO: we need to send the amount associated with the payment as this
        //       will determine the payment methods. Also, in the future we will
        //       need to send the country with the amount.
        App.PaymentMethod.find().then(
            // Success
            function(methods) {
                _this.set('methods', methods);
            },
            // Failure
            function(methods) {
                throw new Em.error('Fetching PaymentMethod\'s failed!');
            }
        );
    },

    _processPaymentMetadata: function () {
        // integration_url (at PSP)
        // integration_method (GET/POST/PUT)
        // integration_payload (optional metadata required by PSP)
        // integration_type (redirect/popup)
        var meta = this.get('model.integrationDetails');

        if (meta.type == 'redirect') {
            if (meta.method == 'get') {
              window.location.replace(meta.url);
            }
        }
    },

    actions: {
        nextStep: function () {
            var _this = this,
                payment = this.get('model');

            payment.save().then(
                // Success
                function (payment) {
                    // Reload the order to receive any backend updates to the order status
                    // NOTE: when using the mock api we will need to manually set the order
                    //       status here.
                    payment.get('order').then(function (order) {
                        order.reload();
                    });

                    // Proceed to the next step based on the status of the payment
                    // 1) Payment status is 'success'
                    // 2) Payment status is 'in_progress'
                    if (payment.get('success')) {
                        // Load the success modal
                        _this.send('modalSlide', 'paymentSuccess', payment);
                    } else {
                        _this._processPaymentMetadata();
                    }
                },
                // Failure
                function (payment) {

                }
            );
        }
    }
});

// TODO: Adding controllers here for payment success/pending so that the modal 
//       will work with the bb_modal code.
App.PaymentPendingController = Em.Controller.extend();

App.PaymentSuccessController = Em.ObjectController.extend(BB.ModalControllerMixin, {
});
