App.SuggestionController = Em.ObjectController.extend({

    updateSuggestion: function(project) {
        var model = this.get('model');
        model.set('status', 'in_progress');
        model.set('project', project);
        model.save();
    },

    createProject: function() {
        var model = this.get('model');

        var project = App.MyProject.createRecord({
            title: model.get('title'),
            pitch: model.get('pitch'),
            theme: model.get('theme')
        });
        project.save();
        return project;
    },

    actions: {

        adoptSuggestion: function() {
            
            this.send('closeModal');

            var project = this.createProject();
            
            this.updateSuggestion(project);

            // Redirect to project edit flow
            this.transitionTo('myProject.pitch', project)

        }
    }
});

App.SuggestionListController = Em.ArrayController.extend({
    totalSuggestions: function() {
        return this.get('model.length');
    }.property("@each"),

    hasSuggestions: function() {
        return this.get('totalSuggestions') > 0;
    }.property('totalSuggestions'),

    actions: {
        showSuggestion: function(suggestion) {
            this.send('openInExtraLargeBox', "suggestion", suggestion);
        }
    }
});

