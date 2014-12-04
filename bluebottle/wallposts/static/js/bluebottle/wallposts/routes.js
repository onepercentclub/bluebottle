App.WallRouteMixin = Em.Mixin.create({

    parentId: '',
    parentType: '',
    wallpostPage: null,
    wallpostTotal: null,

    wallpostRemaining: function(){
        var remaining = this.get('wallpostTotal') - 5 * this.get('wallpostPage');
        if (remaining < 0) return 0;
        return remaining;
    }.property('wallpostPage', 'wallpostTotal'),

    setupController: function(controller, model) {
        this._super(controller, model);

        // Only reload wall-posts if switched to another page.
        var _this = this,
            parentType = this.get('parentType'),
            parentId = model.get('id');

        // Initiate wallposts
        if (this.get('parentId') != parentId || this.get('parentType') != parentType){
            this.set('parentId', parentId);
            this.set('parentType', parentType);
            var store = this.get('store');
            store.find('wallPost', {'parent_type': parentType, 'parent_id': parentId}).then(function(posts){
                _this.set('wallpostTotal', posts.get('meta.total'));
                _this.set('wallpostPage', 1);
                controller.set('wallpostList', posts);
                controller.set('wallpostFiles', Em.A());
                controller.set('wallpostRemaining', _this.get('wallpostRemaining'));
            });
            this._createNewWallposts();
        }
    },

    _createNewWallposts: function (){
        var _this = this,
            parentType = this.get('parentType'),
            parentId = this.get('controller.model.id'),
            controller = this.get('controller'),
            store = this.store.get('store');

        controller.set('newTextWallpost',
            App.TextWallPost.createRecord({'parent_id': parentId, 'parent_type': parentType})
        );
        controller.set('newMediaWallpost',
            App.MediaWallPost.createRecord({'parent_id': parentId, 'parent_type': parentType})
        );
    },

    _connectFilesToWallpost: function (wallpost) {
        var _this = this,
            controller = this.get('controller');
        Ember.run.next(function() {
            if (controller.get('wallpostFiles').length) {
                // Connect all photos to this wallpost.
                controller.get('wallpostFiles').forEach(function(photo){
                    photo.set('mediawallpost', wallpost);
                    photo.save();
                });
                // Empty this.files so we can use it again.
                controller.set('wallpostFiles', Em.A());
            }
        });
    },


    actions: {
        showMoreWallposts: function(){
            var _this = this,
                parentType = this.get('parentType'),
                parentId = this.get('controller.model.id'),
                controller = this.get('controller'),
                wallpostPage = _this.incrementProperty('wallpostPage'),
                store = this.get('store');

            controller.set('wallpostRemaining', _this.get('wallpostRemaining'));

            store.find('wallPost', {'parent_type': parentType, 'parent_id': parentId, 'page': wallpostPage}).then(function(posts){
                controller.get('wallpostList').addObjects(posts);
            });
        },

        addWallpost: function(wallpost){
            var _this = this,
                controller = this.get('controller');
            return wallpost.save().then(function(record){
                // Wallpost saved successfully
                if (controller.get('wallpostFiles')){
                    _this._connectFilesToWallpost(record)
                }
                // Add it to the wallpost list
                controller.get('wallpostList').unshiftObject(record);
                // Create new wallposts for the form.
                _this._createNewWallposts();
            }, function(){
                // Error saving wallpost
            });

            return wallpost.save();
        },
        removeWallpost: function(wallpost){
            wallpost.deleteRecord();
            wallpost.save();
        },
        addWallpostFile: function(file) {
            var _this = this,
                controller = this.get('controller'),
                photo = App.WallPostPhoto.createRecord();

            photo.set('photo', file);
            photo.save();
            // Store the photo in this.files. We need to connect it to the wallpost later.
            photo.on('didCreate', function(record){
                controller.get('wallpostFiles').pushObject(photo);
            });
        },
        removeWallpostFile: function(file) {
            var _this = this,
                controller = this.get('controller');
            file.deleteRecord();
            file.save();
            // Remove it from temporary array too.
            controller.get('wallpostFiles').removeObject(file);
        },
        addWallpostComment: function(comment) {
            comment.save();
        },
        removeWallpostComment: function(comment) {
            comment.deleteRecord();
            comment.save();
        }
    }
});