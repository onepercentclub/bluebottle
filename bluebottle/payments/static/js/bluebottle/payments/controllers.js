App.PaymentController = Em.ObjectController.extend({
    willOpen: function () {
        var _this = this,
            controller = this.get('controller'),
            payment = this.get('model'),
            order = payment.get('order');

        // Reload the order to receive any backend updates to the order status
        // NOTE: when using the mock api we will need to manually set the order
        //       status here.
        if (order) order.reload();

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
    }
});