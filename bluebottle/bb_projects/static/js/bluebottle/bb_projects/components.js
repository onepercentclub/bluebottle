/**
 * Adds an animated progressbar.
 *
 * Usage:
 * {{bb-progressbar totalValue=100 currentValue=50}}
 */
App.BbProgressbarComponent = Ember.Component.extend({
    didInsertElement: function(){
        this.$('.slider-progress').css('width', '0px');
        var width = 0;
        if (this.targetValue > 0) {
        	if(this.currentValue >= this.targetValue){
        		width = 100;
        	} else {
	            width = 100 * this.currentValue / this.targetValue;
        	}
            width += '%';
        }
        this.$('.slider-progress').animate({'width': width}, 1000);
    }
});


App.BbDatepickerComponent = Ember.Component.extend({
});


