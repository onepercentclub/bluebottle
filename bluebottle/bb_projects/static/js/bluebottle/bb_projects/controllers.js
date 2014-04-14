App.ProjectListController = Em.ArrayController.extend({
    needs: ['projectSearchForm']
});


App.ProjectSearchFormController = Em.ObjectController.extend({
    needs: ['projectList'],

    // Number of results to show on one page
    pageSize: 8,


    // Have a property for this so we can easily use another list controller if we extend this.
    listController: function(){
        return this.get('controllers.projectList');
    }.property(),

    init: function(){
        // Make sure this record is in it's own transaction so it will never pollute other commits.
        var transaction = this.get('store').transaction();
        var form =  transaction.createRecord(App.ProjectSearch);
        this.set('model', form);
        this.updateSearch();
    },

    rangeStart: function(){
        return this.get('page') * this.get('pageSize') - this.get('pageSize') + 1;
    }.property('listController.model.length'),

    rangeEnd: function(){
        return this.get('page') * this.get('pageSize') - this.get('pageSize') + this.get('listController.model.length');
    }.property('listController.model.length'),

    hasNextPage: function(){
        var next = this.get('page') * this.get('pageSize');
        var total = this.get('listController.model.meta.total');
        return (next < total);
    }.property('listController.model.meta.total'),

    hasPreviousPage: function(){
        return (this.get('page') > 1);
    }.property('page'),

    orderedByPopularity: function(){
        return (this.get('ordering') == 'popularity');
    }.property('ordering'),
    orderedByTitle: function(){
        return (this.get('ordering') == 'title');
    }.property('ordering'),
    orderedByNewest: function(){
        return (this.get('ordering') == 'newest');
    }.property('ordering'),
    orderedByNeeded: function(){
        return (this.get('ordering') == 'money_needed');
    }.property('ordering'),
    orderedByDeadline: function(){
        return (this.get('ordering') == 'deadline');
    }.property('ordering'),

    updateSearch: function(sender, key){
        if (key != 'page') {
            // If the query changes we should jump back to page 1
            this.set('page', 1);
        }
        if (this.get('model.isDirty') ) {
            var list = this.get('listController');
            var controller = this;

            var query = {
                'page_size': this.get('pageSize'),
                'page': this.get('page'),
                'ordering': this.get('ordering'),
                'status': this.get('status'),
                'country': this.get('country'),
                'text': this.get('text'),
                'theme': this.get('theme')
            };
            var projects = App.ProjectPreview.find(query);
            list.set('model', projects);
        }
    }.observes('text', 'country', 'theme', 'status', 'page', 'ordering'),

    actions: {
        nextPage: function(){
            this.incrementProperty('page');
        },

        previousPage: function(){
            this.decrementProperty('page');
        },

        sortOrder: function(order) {
            this.set('ordering', order);
        },
        clearForm: function(sender, key) {
            this.set('model.text', '');
            this.set('model.country', null);
            this.set('model.theme', null);
            this.set('model.phase', null);
        }

    }
});


App.ProjectController = Em.ObjectController.extend({
    needs: ['projectIndex', 'currentUser'],

    isFundable: function(){
       return (this.get('phase') == 'campaign' && this.get('campaign.money_asked'));
    }.property('phase', 'campaign'),

    allTags: function() {
        var tags = this.get('plan.tags');
        return tags.reduce(function(previousValue, tag, index) {
            var separator = (index == 0 ? " " : ", ");
            return previousValue + separator + tag.id;
        }, "");
    }.property('tags.@each'),

    isProjectOwner: function() {
        var username = this.get('controllers.currentUser.username');
        var ownername = this.get('model.owner.username');
        if (username) {
            return (username == ownername);
        }
        return false;
    }.property('model.owner', 'controllers.currentUser.username')

});

App.ProjectPlanController = Ember.ObjectController.extend(App.StaticMapMixin, {});

App.ProjectSupporterListController = Em.ArrayController.extend({
    supportersLoaded: function(sender, key) {
        if (this.get(key)) {
            this.set('model', this.get('supporters').toArray());
        } else {
            // Don't show old content when new content is being retrieved.
            this.set('model', null);
        }
    }.observes('supporters.isLoaded')

});

App.ProjectIndexController = Em.ArrayController.extend({
    needs: ['project', 'currentUser'],
    perPage: 5,
    page: 1,
    parentId: null,
    parentType: 'project',
    showingAll: null,

    isProjectOwner: function(){
        return this.get('controllers.project.owner.username') == this.get('controllers.currentUser.username');
    }.property('controllers.project.model.owner', 'controllers.currentUser.username'),

    remainingItemCount: function(){
        if (this.get('meta.total')) {
            return this.get('meta.total') - (this.get('page')  * this.get('perPage'));
        }
        return 0;
    }.property('page', 'perPage', 'meta.total'),

    canLoadMore: function(){
        var totalPages = Math.ceil(this.get('meta.total') / this.get('perPage'));
        return totalPages > this.get('page');
    }.property('perPage', 'page', 'meta.total'),

    canAddMediaWallPost: function() {
        var username = this.get('controllers.currentUser.username');
        var ownername = this.get('controllers.project.model.owner.username');
        if (username) {
            return (username == ownername);
        }
        return false;
    }.property('controllers.project.model.owner', 'controllers.currentUser.username'),
    
    getTasks: function() {
        var controller = this;
        if (!this.get("showingAll")) {
            var now = new Date();
            App.Task.find({project: this.get('controllers.project.id')}).then(function(tasks) {
                controller.set("tasks", tasks.filter(function(item) {
                    return (item.get("isStatusOpen") || item.get("isStatusInProgress")) && item.get("people_needed") > item.get("membersCount") && item.get('deadline') > now;
                })); 
             });
        } else {
            controller.set("tasks", App.Task.find({project: this.get('controllers.project.id')}));
        }
    }.observes('showingAll'),

    tasks: function () {
        return App.Task.find({project: this.get('parentId')});
    }.property('parentId'),

    availableTasks: function () {
        return this.get('tasks').filter(function(task) {
            return task.get("isAvailable");
        });
    }.property('tasks.@each.status'),

    unavailableTasks: function () {
        return this.get('tasks').filter(function(task) {
            return task.get("isUnavailable");
        });
    }.property('tasks.@each.status'),


    resetShowingAll: function() {
        this.set("showingAll", false);
    }.observes('parentId'),
    
    actions: {
        showMore: function() {
            var controller = this;
            var page = this.incrementProperty('page');
            var parent_id = this.get('parentId');
            var parent_type = this.get('parentType');
            App.WallPost.find({'parent_type': parent_type, 'parent_id': parent_id, page: page}).then(function(items){
                controller.get('model').pushObjects(items.toArray());
            });
        },
        showActiveTasks: function() {
            this.set("showingAll", false);
        },
        showAllTasks: function() {
            this.set("showingAll", true);
        }
    }
});

App.GenericFieldController = Em.ObjectController.extend({});

/*
 Project Manage Controllers
 */

App.MoveOnMixin = Ember.Mixin.create({

    actions : {
        goToStep: function(step){
            $("body").animate({ scrollTop: 0 }, 600);
            var controller = this;
            if (step) controller.transitionToRoute(step);
        },

        goToPreviousStep: function(){
            var step = this.get('previousStep');
            this.send('goToStep', step);
        },

        goToNextStep: function(){
            var step = this.get('nextStep');
            this.send('goToStep', step);
        }

    }

});

App.MyProjectListController = Em.ArrayController.extend({
    needs: ['currentUser'],
    canPitchNew: function(){
        var can = true;
        this.get('model').forEach(function(project){
            if (project.get('inProgress')) {
                can = false;
            }
        });
        return can;
    }.property('model.@each.phase')

});

App.MyProjectController = Em.ObjectController.extend({
    needs: ['currentUser', 'myProjectOrganisation'],

    // Create a one way binding so that changes in the MyProject controller don't alter the value in
    // the MyProjectOrganization controller. This way the MyProjectOrganization controller is in 
    // control of the value
    myOrganization: null,
    myOrganizationBinding: Ember.Binding.oneWay("controllers.myProjectOrganisation.model"),

    // Here the controller will observe the organization value from the MyProjectOrganization controller
    // and update the connection to the property on the MyProject when the value changes.
    // Use the 'id' property from the organization to ensure it has been comitted and the record returned
    // by the api with a valid id
    connectOrganization: function () {
        var organization = this.get('myOrganization'),
            project = this.get('model');

        // Return early if organization already associated with 
        // project or the organization hasn't been saved yet
        if (organization == project.get('organization') || !organization.get('id'))
            return;

        // Set organization on project.
        project.set('organization', organization);
        if (!project.get('title'))
            project.set('title', organization.get('title'));

        project.save();
    }.observes('myOrganization.id'),

    canPreview: function () {
        return !!this.get('model.title');
    }.property('model.title'),

	isSubmittable: function(){
		return (this.get('isPhasePlanNew') || this.get('isPhaseNeedsWork'))
	}.property('isPhasePlanNew', 'isPhaseNeedsWork'),


    validOrganization: function () {
        var organization = this.get('myOrganization'),
            project = this.get('model');

        if (organization && organization == project.get('organization')) {
            return organization.get('validOrganization');
        } else {
            return project.get('organization.validOrganization');
        }
    }.property('myOrganization', 'model.organization')
});

App.MyProjectStartController = Em.ObjectController.extend(App.MoveOnMixin, {
    needs: ['currentUser'],

    nextStep: 'myProject.pitch'
});

App.MyProjectPitchController = App.StandardTabController.extend({
    previousStep: 'myProject.start',
    nextStep: 'myProject.story',

    canSave: function () {
        return !!this.get('model.title');
    }.property('model.title'),

	allThemes: function(){
        return App.Theme.find();
    }.property(),

    languages: function () {
        return App.Language.find();
    }.property(),

    hasLanguages: function () {
        return this.get('languages.length');
    }.property('languages.length'),

    currentLanguage: function () {
        var results = App.Language.filter( function (language) { 
            return language.get('code') === App.get("language");
        });

        if (results.get('length') > 0) {
            return App.Language.find(results.get('content.0.id'));
        }

        return null;
    }.property('App.language', 'languages.length')
});

App.MyProjectStoryController = App.StandardTabController.extend({
    previousStep: 'myProject.pitch',
    nextStep: 'myProject.organisation',

    canSave: function () {
        return !!this.get('model.title');
    }.property('model.title')
});

App.MyProjectSubmitController = App.StandardTabController.extend({
    needs: ['myProjectOrganisation'],
    previousStep: 'myProject.organisation',

    validSubmit: function () {
        return !this.get('model.isNew') && !this.get('controllers.myProjectOrganisation.model.isNew');
    }.property('controllers.myProjectOrganisation.model.isNew', 'model.isNew'),

    missingFieldsOrganization: function () {
        return this.get('controllers.myProjectOrganisation.model.missingFieldsOrganization');
    }.property('controllers.myProjectOrganisation.model.missingFieldsOrganization'),

    actions: {
        submitPlan: function(e) {
            var controller = this;
            var model = this.get('model');

            // Go to second status/phase
            model.set('status', App.ProjectPhase.find().objectAt(1));

            if (model.get('isNew')) {
                model.transitionTo('loaded.created.uncommitted');
            } else {
                model.transitionTo('loaded.updated.uncommitted');
            }

            // Associate the organization with the project if the
            // organization has been saved => not isNew
            // We have been storing the organization in the route
            // TODO: should we move this to the controller??
            var organization = this.get('controllers.myProjectOrganisation.model');

            if (!organization.get('isNew'))
                model.set('organization', organization);

            model.on('didUpdate', function() {
                controller.transitionToRoute('myProjectReview');
            });
            
            model.save();
        }
    },

    exit: function(){
        this.set('model.status', 'new');
        this._super();
    }
});

