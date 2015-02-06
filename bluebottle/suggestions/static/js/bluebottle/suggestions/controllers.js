App.SuggestionController = Em.ObjectController.extend({});

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

