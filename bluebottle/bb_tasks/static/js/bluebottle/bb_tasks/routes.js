App.Router.map(function(){
    this.resource('taskList', {path: '/tasks'}, function() {
        this.route('search');
    });

    this.resource('myTaskList', {path: '/my/tasks'});
    this.resource('task', {path: '/tasks/:task_id'});
    this.resource('taskEdit', {path: '/tasks/:task_id/edit'});
    this.resource('projectTask', {path: '/:task_id'}, function(){});
    this.resource('taskNew', {path: '/tasks/new/:project_id'});

});



// Tasks

App.ProjectTasksIndexRoute = Em.Route.extend({
    model: function(params) {
        return Em.A();
    },

    setupController: function(controller, model) {
        this._super(controller, model);
        var project = this.modelFor('project');
        var tasks = App.Task.find({project: project.get('id')});
        tasks.addObserver('isLoaded', function() {
            tasks.forEach(function(record) {
                if (record.get('isLoaded')) {
                    controller.get('content').pushObject(record);
                }
            });
        });
    }
});


App.TaskRoute = Em.Route.extend(App.ScrollToTop, App.WallRouteMixin, {

    parentType: 'task',

    model: function(params) {
        return App.Task.find(params.task_id);
    },

    afterModel: function(model){
        if (this.get('tracker')) {
            this.get('tracker').trackEvent("Task detail", {title: model.get('title')});
        }
    },

    actions: {
        applyForTask: function() {
            if (! this.get('currentUser.username')) {
                this.send('openInBox', 'login');
                return;
            }

            var route = this,
                store = route.get('store'),
                taskMember = store.createRecord(App.TaskMember),
                task = this.modelFor('task'),
                view = App.TaskMemberApplyView.create();

			if (!this.controllerFor('task').get('isMember')){
				Bootstrap.ModalPane.popup({
					heading: gettext('Apply for task'),
					bodyViewClass: view,
					primary: gettext('Apply'),
					secondary: gettext('Cancel'),
					callback: function(opts, e) {
						e.preventDefault();
						if (opts.primary) {
							taskMember.set('motivation', view.get('motivation'));
							taskMember.set('task', task);
							taskMember.set('created', new Date());
							taskMember.save();

							if (route.get('tracker')) {
							    route.get('tracker').trackEvent("Apply for task", {task: task.get('title')});
							}
						}
						if (opts.secondary) {
							taskMember.deleteRecord();
						}
					}
				});
			}
        },
        uploadFile: function(task) {
            var route = this;
            var controller = this.controllerFor('taskFileNew');
            var view = App.TaskFileNewView.create();
            view.set('controller', controller);
            var store = route.get('store');
            var file = store.createRecord(App.TaskFile);
            controller.set('model', file);
            file.set('task', task);

            Bootstrap.ModalPane.popup({
                classNames: ['modal', 'large'],
                headerViewClass: Ember.View.extend({
                    tagName: 'p',
                    classNames: ['modal-title'],
                    template: Ember.Handlebars.compile('{{view.parentView.heading}}')
                }),
                heading: task.get('title'),
                bodyViewClass: view,
                primary: 'Save',
                secondary: 'Cancel',
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        file.save();
                    }
                    if (opts.secondary) {
                        file.deleteRecord();
                    }
                }
            });
        },
        editTaskMember: function(taskMember) {
            var route = this;
            var controller = this.controllerFor('taskMemberEdit');
            controller.set('model', taskMember);
            var view = App.TaskMemberEdit.create();
            view.set('controller', controller);

            Bootstrap.ModalPane.popup({
                headerViewClass: Ember.View.extend({
                    tagName: 'p',
                    classNames: ['modal-title'],
                    template: Ember.Handlebars.compile('{{view.parentView.heading}}')
                }),
                heading: taskMember.get('member.full_name'),
                bodyViewClass: view,
                primary: 'Save',
                secondary: 'Cancel',
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        taskMember.save();
                    }
                    if (opts.secondary) {
                        taskMember.rollback();
                    }
                }
            });
        }
    }
});


App.TaskListIndexRoute = Em.Route.extend(App.UsedCountrySelectViewMixin, App.TrackRouteActivateMixin, {
    trackEventName: 'Browse tasks',
    setupController: function(controller, model) {
        this._super(controller, model);
        App.UsedSkill.find().then(function(skill_list){
            App.UsedSkillSelectView.reopen({
                content: skill_list
            });
        });
    }
});


App.TaskNewRoute = Em.Route.extend({
    beforeModel: function (transition) {
        var _this = this,
            projectId = transition.params.project_id;

        return App.Project.find(projectId).then(function (project) {
            _this.set('project', project);
        });
    },

    model: function(params){
        var task = this.get('store').createRecord(App.Task);
        task.set('project', this.get('project'));

        return task;
    }
});



App.TaskEditRoute = Em.Route.extend({
    model: function(params) {
        return App.Task.find(params.task_id);
    }
});

/**
 * My Tasks: manage your tasks
 *
 */

App.MyTaskListRoute = Em.Route.extend(App.ScrollToTop, {
    setupController: function(controller, model){
        var _this = this;
        controller.set('ownerTasks', App.Task.find({'author': 2}));
        controller.set('memberTasks',  App.MyTaskMember.find());

    }

});

