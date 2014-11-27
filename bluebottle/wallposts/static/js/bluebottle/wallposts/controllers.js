
App.WallpostListController = Em.Controller.extend({
    meta: {},

    page: 1,
    total: function(){
        return this.get('meta.total');
    }.property('meta'),

    remainingItemCount: function(){
        return this.get('total') - 5 * this.get('page');
    }.property('total', 'page'),

    canLoadMore: function(){
        return this.get('remainingItemCount') > 0;
    }.property('remainingItemCount'),

    canAddMediaWallpost: false,

    init: function() {
        var _this = this,
            parentType = this.get('parentType'),
            parentId = this.get('parentId');
        debugger;
        this._super();
        App.WallPost.find({'parent_type': parentType, 'parent_id': parentId}).then(function(posts){
            _this.set('posts', posts);
            _this.set('meta', posts.get('meta'));
        });
    },

    actions: {
        showMore: function(){
            var _this = this,
                parentType = this.get('parentType'),
                parentId = this.get('parentId');
            var page = this.incrementProperty('page');
            App.WallPost.find({'parent_type': parentType, 'parent_id': parentId, 'page': page}).then(function(posts){
                _this.get('posts').addObjects(posts);
            });
        }
    }

});