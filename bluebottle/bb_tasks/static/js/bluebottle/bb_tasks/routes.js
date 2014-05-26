App.Router.map(function(){
    this.resource('taskList', {path: '/tasks'}, function() {
        this.route('search');
    });

    // route disabled for now, let the backend handle the hours spent
    // this.resource('myTaskList', {path: '/my/tasks'});
    this.resource('task', {path: '/tasks/:task_id'}, function(){

    });
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


App.TaskRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        return App.Task.find(params.task_id);
    },

    actions: {
        applyForTask: function() {
            var route = this;
            var store = route.get('store');
            var taskMember = store.createRecord(App.TaskMember);
            var task = this.modelFor('task');
            var view = App.TaskMemberApplyView.create();

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


App.TaskListIndexRoute = Em.Route.extend(App.UsedCountrySelectViewMixin, {
    setupController: function(controller, model) {
        this._super(controller, model);
        App.UsedSkill.find().then(function(skill_list){
            App.UsedSkillSelectView.reopen({
                content: skill_list
            });
        });
    }
});


App.TaskIndexRoute = Em.Route.extend(App.WallRouteMixin, {
    parentId: function(){
        return this.modelFor('task').get('id');
    }.property(),
    parentType: 'task'
});


App.TaskNewRoute = Em.Route.extend({
    model: function(params){
        var task = this.get('store').createRecord(App.Task);
        task.set('project', App.Project.find(params.project_id));
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
    model: function(params) {
        return App.MyTaskMember.find();
    }
});

