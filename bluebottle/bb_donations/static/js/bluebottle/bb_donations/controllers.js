App.DonationModalController = Em.ObjectController.extend({
    actions: {
        changeAmount: function(amount){
            this.set('amount', amount);
        }
    }

});