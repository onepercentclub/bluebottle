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

    init: function() {
        this._super();

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
    orderedByDeadline: function(){
        return (this.get('ordering') == 'deadline');
    }.property('ordering'),

    updateSearch: function(sender, key){
        if (key != 'page') {
            // If the query changes we should jump back to page 1
            this.set('page', 1);
        }
        if (this.get('model.isDirty')) {
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
            this.set('model.status', null);
        }
    }
});


App.ProjectController = Em.ObjectController.extend(App.WallControllerMixin, {
    projectDonations: null,
    showWallpostHelp: true,
    otherProjectPlan: false,

    backgroundStyle: function(){
        return "background-image:url('" + this.get('image.large') + "');";
    }.property('image.large'),

    isFundable: function(){
       return (this.get('status') == '5' && this.get('campaign.money_asked'));
    }.property('status'),

    allTags: function() {
        var tags = this.get('plan.tags');
        return tags.reduce(function(previousValue, tag, index) {
            var separator = (index == 0 ? " " : ", ");
            return previousValue + separator + tag.id;
        }, "");
    }.property('tags.@each'),

    isOwner: function() {
        var username = this.get('currentUser.username');
        var ownername = this.get('model.owner.username');
        if (username) {
            return (username == ownername);
        }
        return false;
    }.property('model.owner', 'currentUser.username'),

    _setDonations: function () {
        if (this.get('isLoaded')) {
            this.set('projectDonations', App.ProjectDonation.find({project: this.get('id')}));
        }
    }.observes('isLoaded'),

    supporters: function () {
        if (this.get('projectDonations.isLoaded')) {
            // return a unique list of supporters based on donations with users
            return this.get('projectDonations').mapBy('user').filter(function(user) {return user}).uniq();
        } else {
            return null;
        }
    }.property('projectDonations.isLoaded'),

    recentSupporters: function () {
        if (this.get('supporters')) {
            return this.get('supporters').splice(0, 13);
        }
    }.property('supporters.length'),

    projectSupportersBinding: Ember.Binding.oneWay("supporters"),
    projectDonationsBinding: Ember.Binding.oneWay("projectDonations"),

    canEdit: function () {
        return this.get('isStatusCampaign') && this.get('isOwner');
    }.property('isStatusCampaign', 'isOwner'),

    canDonate: function () {
        return !!this.get('amount_asked');
    }.property('amount_asked'),

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

    canAddMediaWallpost: function(){
        return this.get('isOwner');
    }.property('isOwner'),

    availableTasks: function () {
        return this.get('tasks').filter(function(task) {
            return task.get("isAvailable");
        });
    }.property('tasks.@each.isAvailable'),

    unavailableTasks: function () {
        return this.get('tasks').filter(function(task) {
            return task.get("isUnavailable");
        });
    }.property('tasks.@each.isUnavailable'),

    resetShowingAll: function () {
        this.set("showingAll", false);
    }.observes('parentId'),

    projectSupportName: function() {
        return gettext('Support project')
    }.property(),

    projectTitle: function() {
        return gettext('Campaigner');
    }.property(),

    actions: {
        showActiveTasks: function () {
            this.set("showingAll", false);
        },

        showAllTasks: function () {
            this.set("showingAll", true);
        },

        showProfile: function (profile) {
            this.send('openInBigBox', 'userModal', profile);
        }
    }
});

App.ProjectPlanController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.StaticMapMixin, {
    counter: 0,
    hasPdfDownload: true,

    storyWithHeaderIds: function() {
        var story = this.get("story");
        var $story = jQuery("<div>", {html: story});
        var headers = $story.find("h1,h2,h3,h4,h5,h6")
        var controller = this;
        $.each(headers, function() {
            var counter = controller.get("counter");
            counter++;
            $(this).attr("id", "header-" + counter);       
            controller.set("counter", counter);
        });
        return $story.html();
    }.property("story"),

    headerLinks: function() {
        var $html = jQuery("<div>", {html: this.get("storyWithHeaderIds")});
        var elements = $html.find("h1, h2, h3, h4, h5, h6")
        var arr = $.map(elements, function(element) {return {href: "#" + $(element).attr("id"), name: $(element).text()}});
        return arr;
    }.property("story")
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

            if (step) {
                controller.transitionToRoute(step);
            }
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
    canPitchNew: function(){
        var can = true;
        this.get('model').forEach(function(project){
            if (project.get('inProgress')) {
                can = false;
            }
        });
        return can;
    }.property('model.@each.status')

});

App.MyProjectController = Em.ObjectController.extend({
    needs: ['myProjectOrganisation'],

    // A way to automate things in the frontend, not yet used
//	tabs: ['MyProjectStart', 'MyProjectPitch', 'MyProjectStory',
//           'MyProjectOrganisation', 'MyProjectSubmit'],

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

    isSubmittable: Em.computed.or('model.isStatusPlan'),

    validOrganization: function () {
        var organization = this.get('myOrganization'),
            project = this.get('model');

        if (organization && organization == project.get('organization')) {
            return organization.get('validOrganization');
        } else {
            return project.get('organization.validOrganization');
        }
    }.property('myOrganization.validOrganization', 'model.organization.validOrganization')
});

App.MyProjectPitchController = App.StandardTabController.extend({
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
    }.property('model.title'),
});

App.MyProjectSubmitController = App.StandardTabController.extend({

    needs: ['myProjectOrganisation', 'myProject', 'myProjectBank'],
    previousStep: 'myProject.organisation',

    // data has loaded when the project isLoaded and the organization (if set) isLoaded
    hasLoaded: function () {
        return !!this.get('model.isLoaded') && (!this.get('model.organization') || this.get('model.organization.isLoaded'));
    }.property('model.isLoaded', 'model.organization.isLoaded'),

    validSubmit: function () {
        return !this.get('model.isNew') && !this.get('controllers.myProjectOrganisation.model.isNew');
    }.property('controllers.myProjectOrganisation.model.isNew', 'model.isNew'),

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

            // There won't be an organization associated with the myProjectOrganisation
            // controller if the user hasn't loaded the org tab - even if the project has one.
            // So we only set the organization if there is one associated with the controller
            // and it isn't new. 
            if (organization) {
                if (!organization.get('isNew')) {
                    model.set('organization', organization);
                }
            }

            model.on('didUpdate', function() {
                controller.transitionToRoute('myProjectReview');
            });
            
            model.save();
        }
    },

    currentOrganization: function() {
        return (this.get('model.organization') || this.get('controllers.myProjectOrganisation.model'));
    }.property('model.organization.id', 'controllers.myProjectOrganisation.model.id'),

    //TODO: is this needed?
    exit: function(){
        this.set('model.status', 'new');
        this._super();
    }
});



App.ProjectDonationListController = Em.ObjectController.extend({});
