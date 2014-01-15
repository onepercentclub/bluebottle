App.Router.map(function(){
    this.resource('taskList', {path: '/tasks'}, function() {
        this.route('search');
    });

    // route disabled for now, let the backend handle the hours spent
    // this.resource('myTaskList', {path: '/my/tasks'});
    this.resource('task', {path: '/tasks/:task_id'}, function(){

    });
    this.resource('taskEdit', {path: '/tasks/:task_id/edit'});
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
            // var taskCount = controller.get('content').get('length');
            // controller.set('taskCount', taskCount);
        });
    }
});


App.TaskRoute = Em.Route.extend({
    model: function(params) {
        return App.Task.find(params.task_id);
    },
    actions: {
        applyForTask: function(task) {
            var route = this;
            var store = route.get('store');
            var taskMember = store.createRecord(App.TaskMember);
            var view = App.TaskMemberApplyView.create();


            Bootstrap.ModalPane.popup({
                heading: gettext('Apply for task'),
                bodyViewClass: view,
                primary: gettext('Apply'),
                secondary: gettext('Cancel'),
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        taskMember.set('task', task);
                        taskMember.set('motivation', view.get('motivation'));
                        taskMember.set('created', new Date());
                        taskMember.save();
                    }
                }
            });
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
        showMoreWallPosts: function() {
            var controller = this.get('controller');
            var wallPostController = this.controllerFor('taskWallPostList');
            wallPostController.set('canLoadMore', false);
            var page = wallPostController.incrementProperty('page');
            var task = controller.get('model');
            var wps = App.TaskWallPost.find({task: task.get('id'), page: page});
            wps.addObserver('isLoaded', function() {
                wps.forEach(function(record) {
                    if (record.get('isLoaded')) {
                        wallPostController.get('content').pushObject(record);
                    }
                });
                wallPostController.set('canLoadMore', true);
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
        },
        stopWorkingOnTask: function(task) {
            alert('Not implemented. Sorry!');
        }
    }
});


App.TaskIndexRoute = Em.Route.extend({

    // This way the ArrayController won't hold an immutable array thus it can be extended with more wallposts.
    setupController: function(controller, model) {
        // Only reload wall-posts if switched to another project.
        var parentId = this.modelFor('task').get('id');

        if (controller.get('parentId') != parentId){
            controller.set('page', 1);
            controller.set('parentId', parentId);
            var route = this;
            var mediaWallPostNewController = this.controllerFor('mediaWallPostNew');
            var textWallPostNewController = this.controllerFor('textWallPostNew');

            var store = this.get('store');
            store.find('wallPost', {'parent_type': 'task', 'parent_id': parentId}).then(function(items){
                controller.set('meta', items.get('meta'));
                controller.set('model', items.toArray());

                // Set some variables for WallPostNew controllers
                model = controller.get('model');
                mediaWallPostNewController.set('parentId', parentId);
                mediaWallPostNewController.set('parentType', 'task');
                mediaWallPostNewController.set('wallPostList', model);

                textWallPostNewController.set('parentId', parentId);
                textWallPostNewController.set('parentType', 'task');
                textWallPostNewController.set('wallPostList', model);
            });
        }
    }
});


App.TaskNewRoute = Em.Route.extend({
    model: function(params) {
        return this.get('store').createRecord(App.Task);
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

