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

                    _this.send('modalSlide', 'payment', payment, 'modalBack');
                },
                // Failure
                function() {
                    throw new Em.error('Saving Donation failed!');
                }
            );
        }
    }
});


App.ProjectSupporterListController = Em.ArrayController.extend({
    needs: ['project'],

    supporters: function () {
        return App.ProjectDonation.find({project: this.get('controllers.project.id')});
    }.property('controllers.project.id'),

	supportersLoaded: function(sender, key) {
		if (this.get(key)) {
			this.set('model', this.get('supporters').toArray());
		} else {
			this.set('model', null);
		}
	}.observes('supporters.isLoaded')

});
