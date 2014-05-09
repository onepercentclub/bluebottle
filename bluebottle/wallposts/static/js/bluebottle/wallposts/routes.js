App.WallRouteMixin = Em.Mixin.create({

    parentId: Em.K(),
    parentType: Em.K(),
    
    // This way the ArrayController won't hold an immutable array thus it can be extended with more wallposts.
    setupController: function(controller, model) {
        // Only reload wall-posts if switched to another project.
        var parentType = this.get('parentType');
        var parent = this.modelFor(parentType);
        var parentId = parent.id;

        if (controller.get('parentId') != parentId){
            controller.set('page', 1);
            controller.set('parentId', parentId);
            controller.set('parentType', parentType);
            var route = this;
            var mediaWallPostNewController = this.controllerFor('mediaWallPostNew');
            var textWallPostNewController = this.controllerFor('textWallPostNew');

            var store = this.get('store');
            store.find('wallPost', {'parent_type': parentType, 'parent_id': parentId}).then(function(items){
                controller.set('meta', items.get('meta'));
                controller.set('model', items.toArray());

                // Set some variables for WallPostNew controllers
                model = controller.get('model');
                mediaWallPostNewController.set('parentId', parentId);
                mediaWallPostNewController.set('parentType', parentType);
                mediaWallPostNewController.set('wallPostList', model);

                textWallPostNewController.set('parentId', parentId);
                textWallPostNewController.set('parentType', parentType);
                textWallPostNewController.set('wallPostList', model);
            });
        }
    },
});
