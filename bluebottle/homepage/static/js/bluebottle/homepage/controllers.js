
App.HomeController = Ember.ObjectController.extend({
    needs: ['currentUser'],
	project: null,
    isCampaignHomePage: false,
	projectIndex: 0,
    quoteIndex: 0,
    actions: {
        nextProject: function() {
            this.incrementProperty('projectIndex');
        },
    
        prevProject: function() {
            this.decrementProperty('projectIndex');        
        }        
    },
    
    animateSlider: function() {
        console.log('animate')
        var index = this.get('projectIndex');
        var project_count = this.get("projects").get("length");
        console.log(index, project_count);
        $(".project-slides").animate({'margin-left': -(1100 * (index % project_count))})
    }.observes('projectIndex'),

    loadQuote: function() {
        this.set('quote', this.get('quotes').objectAt(this.get('quoteIndex')));
    }
});
