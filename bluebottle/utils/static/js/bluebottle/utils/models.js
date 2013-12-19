// The id will be the tag string.
App.Tag = DS.Model.extend({
    url: 'utils/tags',
    // Hack to make sure that newly added tags won't conflict when they are saved embedded.
    loadedData: function() {
        if (this.get('isDirty') === false) {
            this._super.apply(this, arguments);
        }
    }
});