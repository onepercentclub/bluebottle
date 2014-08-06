/*
* Views
*/

App.DonationView = Em.View.extend({
    keyDown: function(e){
    	var input = this.$().find('.donation-input'),
    		inputVal = input.val();
    	
    	if (inputVal.length > 4) {
    		$(input).addClass('is-long');
    	} else if (inputVal.length <= 4) {
    		$(input).removeClass('is-long');
    	}
    }
})