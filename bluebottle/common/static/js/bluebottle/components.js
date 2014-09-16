App.BbBackdropComponent = Ember.Component.extend({
    backdropStyle: function() {
        return "background: url(" + this.get('bgImage') + ") no-repeat center top;";
    }.property('bgImage'),
});