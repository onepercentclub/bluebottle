App.PaymentController = Em.ObjectController.extend({
    willOpen: function () {
        var _this = this,
            controller = this.get('controller'),
            order = this.get('model');

        // Reload the order to receive any backend updates to the order status
        // TODO: why is order undefined here?
        if (order) order.reload();

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