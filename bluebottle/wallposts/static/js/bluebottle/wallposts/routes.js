App.WallRouteMixin = Em.Mixin.create({

    parentId: '',
    parentType: '',
    wallpostPage: 1,

    setupController: function(controller, model) {
        this._super(controller, model);

        // Only reload wall-posts if switched to another page.
        var parentType = this.get('parentType');
        var parent = this.modelFor(parentType);
        var parentId = parent.id;

        if (controller.get('parentId') != parentId || textWallPostNewController.set('parentType') != parentType){
            this.set('parentId', parentId);
            this.set('parentType', parentType);
            controller.set('wallpostPage', 1);
            var store = this.get('store');
            store.find('wallPost', {'parent_type': parentType, 'parent_id': parentId}).then(function(posts){
                controller.set('wallpostTotal', posts.get('meta.total'));
                controller.set('wallpostList', posts);
            });
        }
    },

    actions: {
        showMoreWallposts: function(){
            var parentType = this.get('parentType'),
                parentId = this.get('controller.model.id'),
                wallpostPage = this.incrementProperty('wallpostPage'),
                controller = this.get('controller'),
                store = this.get('store');

            controller.set('wallpostPage', wallpostPage);
            store.find('wallPost', {'parent_type': parentType, 'parent_id': parentId, 'page': wallpostPage}).then(function(posts){
                controller.set('wallpostTotal', posts.get('meta.total'));
                controller.get('wallpostList').addObjects(posts);
            });
        },

        addWallpost: function(wallpost){
            return wallpost.save();
        },
        removeWallpost: function(wallpost){
            return wallpost.delete();
        }
    }
});