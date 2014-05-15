/**
 *  Router Map
 */

App.Router.map(function(){
    this.resource('projectList', {path: '/projects'}, function() {
        this.route('search');
    });

    this.resource('project', {path: '/projects/:project_id'}, function() {
        this.resource('projectPlan', {path: '/plan'});
        this.resource('projectTasks', {path: '/tasks'}, function(){});
    });

    this.resource('myProjectList', {path: '/my/projects'});

    this.resource('myProject', {path: '/my/projects/:id'}, function() {

        this.route('start');
        this.route('pitch');
        this.route('story');
        this.route('organisation');

        this.route('bank');
        this.route('budget');

        this.route('submit');

    });

    this.resource('myProjectReview', {path: '/my/projects/:id/review'});

});


/**
 * Project Routes
 */

App.ProjectListIndexRoute = Em.Route.extend(App.UsedCountrySelectViewMixin, {
    setupController: function(controller, model) {
        this._super(controller, model);
        App.UsedTheme.find().then(function(theme_list){
            App.UsedThemeSelectView.reopen({
                content: theme_list
            });
        });
    }
});


App.ProjectRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        // Crap hack because Ember somehow doesn't strip query-params.
        // FIXME: Find out this -should- work.
        var project_id = params.project_id.split('?')[0];
        var page =  App.Project.find(project_id);
        var route = this;
        page.on('becameError', function() {
            route.transitionTo('projectList');
        });
        return page;
    }
});


App.ProjectIndexRoute = Em.Route.extend(App.WallRouteMixin, {

    parentId: function(){
        return this.modelFor('project').get('id');
    }.property(),
    parentType: 'project'
});


/**
 * My Projects
 * - Manage your project(s)
 */

App.MyProjectListRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        return App.MyProject.find();
    },
    setupController: function(controller, model) {
        this._super(controller, model);
    }

});
 

App.MyProjectRoute = Em.Route.extend({
    // Load the Project
    model: function(params) {
        var store = this.get('store');
        if (params.id == 'new' || params.id == 'null') {
            return App.MyProject.createRecord();
        }
        var project = store.find('myProject', params.id);

        return project;
    }
});

App.MyProjectIndexRoute = Em.Route.extend({
    redirect: function(){
        this.transitionTo('myProject.pitch');
    }

});


App.MyProjectSubRoute = Em.Route.extend(App.SaveOnTransitionRouteMixin, App.ScrollToTop, {
    skipExitSignal: false,

    redirect: function() {
        var phase = this.modelFor('myProject').get('phase');
        switch(phase) {
            case 'plan-submitted':
                this.transitionTo('myProjectReview');
                break;
            case 'plan-rejected':
                this.transitionTo('myProjectRejected');
                break;
        }
    },

    model: function(params) {
        return this.modelFor('myProject');
    }
});

App.MyProjectStartRoute = App.MyProjectSubRoute.extend({
    skipExitSignal: true,

    redirect: function() {
        var phase = this.modelFor('myProject').get('phase');
        switch(phase) {
            case 'plan-submitted':
                this.transitionTo('myProjectReview');
                break;
            case 'plan-rejected':
                this.transitionTo('myProjectRejected');
                break;
        }
    },

    model: function(params) {
        return this.modelFor('myProject');
    }
});

App.MyProjectPitchRoute = App.MyProjectSubRoute.extend({});
App.MyProjectStoryRoute = App.MyProjectSubRoute.extend({});
App.MyProjectLocationRoute = App.MyProjectSubRoute.extend({});
App.MyProjectMediaRoute = App.MyProjectSubRoute.extend({});
App.MyProjectCampaignRoute = App.MyProjectSubRoute.extend({});
App.MyProjectDetailsRoute = App.MyProjectSubRoute.extend({
    setupController: function(controller, model) {
        this._super(controller, model);
        controller.set('fields', App.ProjectDetailField.find());
    }
});
App.MyProjectSubmitRoute = App.MyProjectSubRoute.extend({skipExitSignal: true});

App.MyProjectBudgetRoute = App.MyProjectSubRoute.extend({
    setupController: function(controller, model){
        this._super(controller, model);

        var numBudgetLines = model.get('budgetLines').get('content').length;
        if(numBudgetLines === 0){
            Em.run.next(function(){
                controller.send('addBudgetLine');
            });
        } else {
            // there are budget lines, and it's not the initial click -> show errors
            controller.set('showBudgetError', true);
        }
    }
});

App.MyProjectOrganisationRoute = App.MyProjectSubRoute.extend({
    model: function(params) {
        var project = this.modelFor('myProject');

        if (project.get('organization')) {
            return project.get('organization');
        } else {
            return App.MyOrganization.createRecord();
        }
    },

    setupController: function (controller, model) {
      this._super(controller, model);

      controller.set('organizations', App.MyOrganization.find());
    }
});

App.MyProjectBankRoute = App.MyProjectSubRoute.extend({
    model: function(params) {
        var project = this.modelFor('myProject'),
        organization = this.modelFor('myProjectOrganization');

        if (organization) {
            return organization;
        } else if (project.get('organization')) {
            return project.get('organization');
        } else {
            return App.MyOrganization.createRecord();
        }
    }
});

App.MyProjectReviewRoute = App.MyProjectRoute.extend({});

App.ProjectPlanRoute = Em.Route.extend({
    model: function(){
        var project = this.modelFor("project");
        return project;
    }
});
