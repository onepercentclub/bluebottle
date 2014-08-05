App.DonationController = Em.ObjectController.extend({
    actions: {
        changeAmount: function(amount){
            this.set('amount', amount);
        },

        nextStep: function(){
            var _this = this,
                donation = this.get('model'),
                order = donation.get('order');

            donation.save().then(
                // Success
                function() {
                    var payment = App.MyPayment.createRecord({order: order});

                    _this.send('modalSlide', 'payment', payment);
                },
                // Failure
                function() {
                    throw new Em.error('Saving Donation failed!');
                }
            );
        }
    }
});