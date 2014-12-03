/*
 Controllers
 */


App.TaskListController = Em.ArrayController.extend({
    needs: ['taskSearchForm']
});


App.TaskSearchFormController = Em.ObjectController.extend({
    needs: ['taskList'],

    init: function(){
        var form =  App.TaskSearch.createRecord();
        this.set('model', form);
        this.updateSearch();
    },

    rangeStart: function(){
        return this.get('page') * 8 -7;
    }.property('controllers.taskList.model.length'),

    rangeEnd: function(){
        return this.get('page') * 8 -8 + this.get('controllers.taskList.model.length');
    }.property('controllers.taskList.model.length'),

    hasNextPage: function(){
        var next = this.get('page') * 8 -7;
        var total = this.get('controllers.taskList.model.meta.total');
        return (next < total);
    }.property('controllers.taskList.model.meta.total'),

    hasPreviousPage: function(){
        return (this.get('page') > 1);
    }.property('page'),

    nextPage: function(){
        this.incrementProperty('page');
    },

    previousPage: function(){
        this.decrementProperty('page');
    },

    sortOrder: function(order) {
        this.set('ordering', order);
    },

    orderedByNewest: function(){
        return (this.get('ordering') == 'newest');
    }.property('ordering'),
    orderedByDeadline: function(){
        return (this.get('ordering') == 'deadline');
    }.property('ordering'),

    clearForm: function(sender, key) {
        this.set('model.text', '');
        this.set('model.skill', null);
        this.set('model.status', null);
        this.set('model.country', null);
    },

    updateSearch: function(sender, key){
        if (key != 'page') {
            // If the query changes we should jump back to page 1
            this.set('page', 1);
        }
        if (this.get('model.isDirty') ) {
            var list = this.get('controllers.taskList');
            var controller = this;

            var query = {
                'page': this.get('page'),
                'ordering': this.get('ordering'),
                'status': this.get('status'),
                'country': this.get('country'),
                'text': this.get('text'),
                'skill': this.get('skill.id')
            };
            var tasks = App.TaskPreview.find(query);
            list.set('model', tasks);
        }
    }.observes('text', 'skill', 'status', 'country', 'page', 'ordering')


});


App.IsProjectOwnerMixin = Em.Mixin.create({
    isProjectOwner: function() {
        var username = this.get('currentUser.username');
        var ownername = this.get('controllers.project.model.owner.username');
        if (username) {
            return (username == ownername);
        }
        return false;
    }.property('controllers.project.model.owner', 'currentUser.username')
});


App.CanEditTaskMixin = Em.Mixin.create({
    canEdit: function() {
        var username = this.get('currentUser.username');
        var author_name = this.get('author.username');
        if (username) {
            return (username == author_name);
        }
        return false;
    }.property('author', 'currentUser.username')
});

App.ProjectTasksIndexController = Em.ArrayController.extend(App.IsProjectOwnerMixin, {
    needs: ['project']
});


App.TaskController = Em.ObjectController.extend(App.CanEditTaskMixin, App.IsAuthorMixin, {
	// you can apply to a task only if:
	// the task is not closed, realized or completed
	// (strange behaviour since completed is not a status but just a label)
	// and if:
	// you are not a already a member or if you already applied
	isApplicable: function(){
		var model = this.get('model');
        if (model.get('isStatusClosed') || model.get('isStatusRealized') || model.get('isStatusCompleted') || model.get('isStatusInProgress')){
            return false;
        }
        if (this.get('isMember')) {
            return false;
        }
        if (this.get('acceptedMemberCount') >=  this.get('people_needed')) {
            return false;

        }
        return true;
	}.property('status', 'isMember', 'model.isStatusClosed', 'model.isStatusRealized', 'model.isStatusCompleted',
		'model.@members.isStatusAccepted'),

    acceptedMemberCount: function(){
        return (this.get('members').filterBy('isAccepted').get('length'));
    }.property('model.members.@each.status'),

    isMember: function() {
        var user = this.get('currentUser.username');
        var isMember = false;
        this.get('model.members').forEach(function(member) {
            var mem = member.get('member.username');
            if (mem == user) {
                isMember =  true;
            }
        });
        return isMember;
    }.property('members.@each.member.username', 'currentUser.username'),

    isOwner: function() {
        var username = this.get('currentUser.username');
        var ownername = this.get('author.username');
        if (username) {
            return (username == ownername);
        }
        return false;
    }.property('author', 'currentUser.username'),

    canUpload: function(){
        return (this.get('isMember') || this.get('isAuthor'));
    }.property('isMember', 'isAuthor'),

    acceptedMembers: function() {
      return this.get('model').get('members').filterBy('isStatusAccepted', true);
    }.property('members.@each.member.isStatusAccepted'),

    notAcceptedMembers: function() {
      return this.get('model').get('members').filterBy('isStatusAccepted', false);
    }.property('members.@each.member.isStatusAccepted'),

    backgroundStyle: function(){
        return "background-image:url('" + this.get('project.image.large') + "');";
    }.property('project.image.large')

});


App.TaskActivityController = App.TaskController.extend({
    needs: ['task', 'taskMember'],

    canEditTask: function() {
        var user = this.get('currentUser.username');
        var author_name = this.get('controllers.task.author.username');
        if (username) {
            return (username == author_name);
        }
        return false;
    }.property('controllers.task.author', 'currentUser.username'),

});


App.TaskMemberController = Em.ObjectController.extend({
    needs: ['task'],

    isStatusApplied: function(){
        return this.get('status') == 'applied';
    }.property('status'),

    isStatusAccepted: function(){
        return this.get('status') == 'accepted';
    }.property('status'),

    isStatusInProgress: function(){
        return this.get('status') == 'in progress';
    }.property('status'),

    isStatusClosed: function(){
        return this.get('status') == 'closed';
    }.property('status'),

    isStatusRealized: function(){
        return this.get('status') == 'realized';
    }.property('status'),

    isCurrentUser: function(){
        var currentUser = this.get('currentUser.username');
        var member = this.get('member.username');
        if (member == currentUser){
            return true;
        }
        return false;
    }.property(),

    // currentUserIsAuthor: function () {
    //     // TODO: move this into a function which can be accessed app-wide => pass a user instance and
    //     //       the result will be true if the user is the current user.
    //     // TODO: we should be injecting the currentUser into all controllers so we can do this.get('currentUser')
    //     //       in the controller and {{ currentUser }} in the templates.
    //     // return (this.get('currentUser.id_for_ember').toString() == this.get('task.author.id'));
    //     return (this.get('currentUser.username') == this.get('task.author.username'));
    // }.property('task.author.id'),

    currentUserIsAuthor: function () {
        // TODO: move this into a function which can be accessed app-wide => pass a user instance and
        //      the result will be true if the user is the current user.
        // TODO: we should be injecting the currentUser into all controllers so we can do this.get('currentUser')
        //      in the controller and {{ currentUser }} in the templates.
        var currentUsername = this.get('currentUser.username'),
            authorUsername = this.get('task.author.username');

        if (! currentUsername || ! authorUsername) {
            return false;
        }

        return (currentUsername == authorUsername);
    }.property('task.author.username', 'currentUser.username'),

    canEditStatus: function(){
        if (this.get('currentUserIsAuthor') && this.get('task') && this.get('task.status') != 'closed' && this.get('task.status') != 'completed'){
            return true;
        }
        return false;
    }.property('task.status'),

    canWithdraw: function(){
        if (this.get('isCurrentUser') && (this.get('isStatusAccepted') || this.get('isStatusApplied')) ){
            return true;
        }
        return false;
    }.property('status'),


    confirmation: function(){
        var task = this.get('task');
        if (task.get('author.id') == this.get('currentUser.id_for_ember') &&
            task.get('isStatusRealized') && this.get('isStatusAccepted')) {
            return true;
        }

        return false;
    }.property('status'),

    actions: {

        declineMember: function( member){
            member.set('status', 'rejected');
            member.save()
        },

        acceptMember: function( member){
            member.set('status', 'accepted');
            member.save()
        },

        confirmMember: function( member){
            member.set('status', 'realized');
            member.save()
        },

        didNotComplete: function( member){
            member.set('status', 'stopped');
            member.save()
        },
        withdrawTaskMember: function(member){
           member.deleteRecord();
           member.save();
        }
    }
});

App.MyTaskMemberController = Em.ObjectController.extend({
    actions: {
        editTimeSpent: function() {
            this.set('isEditing', true);
        }
    },

    isEditing: false
});

App.TaskNewController = Em.ObjectController.extend({

    createTask: function(event){
        var controller = this;
        var task = this.get('content');
        task.on('didCreate', function(record) {
            controller.transitionToRoute('task', task);
            if (controller.get('tracker')) {
                controller.get('tracker').trackEvent("New task", {title: task.get('title')});
            }

        });
        task.on('becameInvalid', function(record) {
            // controller.set('errors', record.get('errors'));
            // Ember-data currently has no clear way of dealing with the state
            // loaded.created.invalid on server side validation, so we transition
            // to the uncommitted state to allow resubmission
            record.transitionTo('loaded.created.uncommitted');
        });

        task.save();
    }
});


App.TaskEditController = App.TaskNewController.extend({

    updateTask: function(event){
        var controller = this;
        var task = this.get('content');
        if (task.get('isDirty') == false){
            controller.transitionToRoute('task', task);
        }
        task.on('didUpdate', function(record) {
            controller.transitionToRoute('task', task);
            if (controller.get('tracker')) {
                controller.get('tracker').trackEvent("Successful task edit", {title: task.get("title")});
            }

        });
        task.on('becameInvalid', function(record) {
            controller.set('errors', record.get('errors'));
        });
        task.save();
    },
    cancelChangesToTask: function(event){
        var task = this.get('content');
        //Don't do a rollback on the object directly, but, via the transaction
        task.get('transaction').rollback();
        this.transitionToRoute('task', task);
    }

});


App.TaskPreviewController = Em.ObjectController.extend({});


App.TaskMemberEditController = Em.ObjectController.extend({});


App.TaskFileNewController = Em.ObjectController.extend({
    addFile: function(file) {
        this.set('model.file', file);
    }
});

