App.DonationModalController = Em.ObjectController.extend({
    actions: {
        changeAmount: function(amount){
            this.set('amount', amount);
        },
        nextStep: function(){
            var donation = this.get('model');
            donation.save().then(
                // Success
                function(){
                    alert('Saved!');
                },
                // Failure
                function(){

                }
            )
        }
    }

});