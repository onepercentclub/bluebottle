App.SuggestionController = Em.ObjectController.extend({
    actions: {
        adoptSuggestion: function(suggestion) {

            App.Theme.find(suggestion.get('theme')).then(function(theme) {
                debugger
                App.MyProject.createRecord({
                    title: suggestion.get('title'),
                    pitch: suggestion.get('pitch'),
                    theme: theme
                }).save().then(function (project) {
                    // Redirect to project edit flow
                    this.transitionTo('myProject.pitch', project)
                });
            });

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

