App.DonationModalController = Em.ObjectController.extend({
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
                function(){
                    _this.send('selectPaymentMethod', order);
                },
                // Failure
                function(){

                }
            )
        }
    }

});