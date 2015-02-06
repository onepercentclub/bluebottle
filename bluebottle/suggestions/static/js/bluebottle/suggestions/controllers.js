App.SuggestionListController = Em.ArrayController.extend({
    totalSuggestions: function() {
        return this.get('model.length');
    }.property("@each"),

    hasSuggestions: function() {
        return this.get('totalSuggestions') > 0;
    }.property('totalSuggestions')
});


App.SuggestionModalController = Em.ObjectController.extend(BB.ModalControllerMixin, {
    init: function() {
        this._super();
    },


});