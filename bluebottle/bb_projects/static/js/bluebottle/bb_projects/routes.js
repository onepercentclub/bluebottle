/**
 *  Router Map
 */

App.Router.map(function(){
    this.resource('projectList', {path: '/projects'}, function() {
        this.route('search');
    });

    this.resource('project', {path: '/projects/:project_id'});

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
    this.resource('projectDonationList', {path: '/projects/:project_id/donations'});

});


/**
 * Project Routes
 */

App.ProjectListIndexRoute = Em.Route.extend(App.UsedCountrySelectViewMixin, App.TrackRouteActivateMixin, {
    trackEventName: "Browse projects",
    setupController: function(controller, model) {
        this._super(controller, model);
        App.UsedTheme.find().then(function(theme_list){
            App.UsedThemeSelectView.reopen({
                content: theme_list
            });
        });
    }


});


App.ProjectRoute = Em.Route.extend(App.ScrollToTop, App.WallRouteMixin, {
    parentType: 'project',

    model: function(params) {
        // Crap hack because Ember somehow doesn't strip query-params.
        // FIXME: Find out this -should- work.
        var project_id = params.project_id.split('?')[0];
        var page =  App.Project.find(project_id);
        var route = this;
        return page;
    },

    afterModel: function(model, transition) {
        if (model.get('isStatusPlan')) {
            this.transitionTo('projectList');
        }
    },

    actions: {
        error: function(error, transition) {
            this.transitionTo('projectList');
        }
    }
});

        var _this = this;

        // FIXME: This isn't the way we should this. In the ProjectIndexRoute we use a App.WallRouteMixin, that
        // uses parent stuff that refers to this controller. However, it calls the parent directly and doesn't
        // handle the promise before the model is loaded. We should refactor the App.WallRouteMixin at some point.
        var promise = App.Project.find(project_id);

        promise.then(function(model) {
            if (_this.get('tracker')) {
                _this.get('tracker').trackEvent("Project detail", {"title": model.get('title')});
            }
        }, function() {
            _this.transitionTo('projectList');
        });

        return promise;
    },
    setupController: function(controller, model){
        this._super(controller, model);

        var parentId = model.get('id');
        controller.set('tasks', App.Task.find({project: parentId}));
    }
});


/**
 * My Projects
 * - Manage your project(s)
 */

App.MyProjectListRoute = Em.Route.extend(App.ScrollToTop, App.TrackRouteActivateMixin, {
    trackEventName: "My Campaigns",
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

App.MyProjectPitchRoute = App.MyProjectSubRoute.extend(App.TrackRouteActivateMixin, {
    trackEventName: "Create Campaign - Pitch"
});
App.MyProjectStoryRoute = App.MyProjectSubRoute.extend(App.TrackRouteActivateMixin, {
    trackEventName: "Create Campaign - Story"
});
App.MyProjectLocationRoute = App.MyProjectSubRoute.extend({

});
App.MyProjectMediaRoute = App.MyProjectSubRoute.extend({});
App.MyProjectCampaignRoute = App.MyProjectSubRoute.extend({});
App.MyProjectDetailsRoute = App.MyProjectSubRoute.extend({
    setupController: function(controller, model) {
        this._super(controller, model);
        controller.set('fields', App.ProjectDetailField.find());
    }
});
App.MyProjectSubmitRoute = App.MyProjectSubRoute.extend(App.TrackRouteActivateMixin, {
    skipExitSignal: true,
    trackEventName: "Create Campaign - Submit"
});

App.MyProjectBudgetRoute = App.MyProjectSubRoute.extend(App.TrackRouteActivateMixin, {
    trackEventName: "Create Campaign - Budget",
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
    },


});

App.MyProjectOrganisationRoute = App.MyProjectSubRoute.extend(App.TrackRouteActivateMixin, {
    trackEventName: "Create Campaign - Organisation",
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
      controller.set('selectedOrganization', null);
    },


});

App.MyProjectBankRoute = App.MyProjectSubRoute.extend(App.TrackRouteActivateMixin, {
    trackEventName: "Create Campaign - Bank",
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
    },


});

App.MyProjectReviewRoute = App.MyProjectRoute.extend(App.TrackRouteActivateMixin, {
    trackEventName: "Create Campaign - Review"
});

App.ProjectPlanRoute = Em.Route.extend({
    model: function(){
        var project = this.modelFor("project");
        return project;
    }
});


App.ProjectDonationListRoute = Em.Route.extend({
    model: function(params) {
        var project_id = params.project_id.split('?')[0];
        return App.Project.find(project_id);
    },

    setupController: function(controller, project) {
        this._super(controller, project);
        controller.set('projectDonations', App.MyProjectDonation.find({project: project.id}));

    }
});
