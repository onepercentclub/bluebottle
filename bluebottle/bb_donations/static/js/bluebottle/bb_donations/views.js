App.DonationView = App.FormView.extend({
    amount: gettext('Amount'),

	keyDown: function(e){
    	var input = this.$().find('.donation-input'),
    		inputVal = input.val();
    	
    	if (inputVal.length > 4) {
    		$(input).addClass('is-long');
    	} else if (inputVal.length <= 4) {
    		$(input).removeClass('is-long');
    	}
    } 
});
