/**
 * write a comment component
 *
 */

App.BbTextWallpostNewComponent = Ember.Component.extend({
    actions: {
        submit: function() {
            this.sendAction("submit");
        }
    }
});

App.BbMediaWallpostNewComponent = App.BbTextWallpostNewComponent.extend();