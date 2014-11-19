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

App.ProjectDonationsComponent = Em.Component.extend({
    limitedDonations: function () {
        if (! this.get('donations.isLoaded')) return;

        var limit = this.get('limit') || 10;
        return this.get('donations').toArray().splice(0, limit);
    }.property('limit', 'donations.isLoaded'),

    actions: {
        show: function(profile) {
            this.sendAction('showProfile', profile);
        }
    }
});

App.SimpleProjectSupportersComponent = Ember.Component.extend({
    limitedSupporters: function () {
        if (! this.get('supporters')) return;

        var limit = this.get('limit') || 10;
        return this.get('supporters').splice(0, limit);
    }.property('limit', 'supporters.length'),

    amountSupporters: function() {
        return this.get('supporters');
    }.property('supporters.length'),

    actions: {
        show: function(profile) {
            this.sendAction('showProfile', profile);
        }
    }
});
