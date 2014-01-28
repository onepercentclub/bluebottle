App.HomeBannerView = Ember.View.extend({
    templateName: 'home_banner',

    didInsertElement: function() {

        // Carousel
        this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });
    }
});


App.HomeProjectListView = Ember.View.extend({
    index: 0,
    templateName: 'home_project_list',
	
    didInsertElement: function() {
        var controller = this.get('controller');
        var projects_count = $(".project-preview").size();
        $(".project-slides").width(projects_count * 1100)
    },    
});


App.HomeQuotesView = Ember.View.extend({
    templateName: 'quote_list',

    didInsertElement: function() {
        var controller = this.get('controller');
        this.initQuoteCycle();
    },

    initQuoteCycle: function() {
        var controller = this.get('controller');
        var view = this;
        
        controller.loadQuote();
        
        
        var quoteIntervalId = setInterval(function() {
            controller.incrementProperty('quoteIndex');
            if (controller.get('quoteIndex') === controller.get('quotes').get('length')) {
                controller.set('quoteIndex', 0);
            }
        
            controller.loadQuote();
        
        }, 5000);
        
        this.set('quoteIntervalId', quoteIntervalId);
    },

    willDestroyElement: function() {
        clearInterval(this.get('quoteIntervalId'));
        this.set('quoteIntervalId', null);
    }
});


App.HomeImpactView = Ember.View.extend({
    templateName: 'home_impact'
});


App.HomeFundraisersView = Ember.View.extend({
    templateName: 'home_fundraisers'
});
