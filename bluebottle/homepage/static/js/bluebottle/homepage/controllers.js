
App.HomeController = Ember.ObjectController.extend({
    needs: ['currentUser'],
	project: null,
    isCampaignHomePage: false,
	projectIndex: 1,
    nextProject: null,

    actions: {
        nextProject: function() { // TODO: similar thing for fundraisers?
            var projects = this.get('projects');

            this.incrementProperty('projectIndex');

            if (this.get('projectIndex') >= projects.get('length')) {
                this.set('projectIndex', 0);
            }

            this.loadProject();
        },
    },
	
    projectTransition: function(){

	var project = this.get('project');
	var nextProject = this.get('nextProject');

	if(nextProject){

	    this.slideProject();

	}else{

	    //First time!

	    $('#project-slide-b').animate({opacity: 'toggle'},0);
	    this.set('nextProject', project);

	}

    }.observes('project'),

    slideProject: function(){

	var slide = $('#project-slide-a');
	var nextSlide = $('#project-slide-b');
	var duration = 500;

	var project = this.get('project');
	
	controller = this;

	var callback = function(){

	    var project = controller.get('project');

	    controller.set('nextProject', project);
	    
	    slide.animate({opacity: 'toggle'}, 0);
	    slide.animate({'margin-left': '0px'}, 0);
	    nextSlide.animate({width: 'toggle'}, 0);
	};

	slide.animate(
	    {'margin-left': '+=1200'},
	    duration,
	    function(){
		slide.animate({opacity: 'toggle'},0);
		nextSlide.animate({width: 'toggle'},duration,callback);
	    });
	
	
	
    },

    loadProject: function() {
        var controller = this;
        var projectId = this.get('projects').objectAt(this.get('projectIndex')).get('id');
        App.Project.find(projectId).then(function(project) {
            controller.set('project', project);
        });
    },

    loadQuote: function() {
        this.set('quote', this.get('quotes').objectAt(this.get('quoteIndex')));
    },
});
