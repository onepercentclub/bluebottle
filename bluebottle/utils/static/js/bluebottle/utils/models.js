// The id will be the tag string.
App.Tag = DS.Model.extend({
    url: 'utils/tags',

    // Hack to make sure that newly added tags won't conflict when they are saved embedded.
    loadedData: function() {
        if (this.get('isDirty') === false) {
            this._super.apply(this, arguments);
        }
    },

    unDirtySoWeNeverCommit: function(){
        // Ugly fix to avoid putting tags
        if (this.get('isDirty')){
           this.transitionTo('loaded.created.uncommitted');
        }
    }.observes('isDirty')

});

