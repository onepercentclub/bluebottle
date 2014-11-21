
App.WallPostController = Em.ObjectController.extend(App.IsAuthorMixin, {
    // Don't show Fundraiser (title/link) on FundRaiser page.
    showFundRaiser: function(){
        if (this.get('parent_type') == 'fundraiser') {
            return false;
        }
        // Show FundRaiser if any.
        return this.get('fundraiser');
    }.property('fundraiser', 'parent_type'),

    newReaction: function(){
        var transaction = this.get('store').transaction();
        return transaction.createRecord(App.WallPostReaction, {'wallpost': this.get('model')});
    }.property('model'),

    actions: {
        editWallPost: function() {
            console.log("edit");
        }
    }
});

App.TaskWallPostListController = Em.ArrayController.extend({
    actions: {
        editWallPost: function() {
            console.log("edit");
        }
    }
});


App.TextWallPostNewController = Em.ObjectController.extend({
    /**
     * This is the base class for a wall-post form.
     *
     * To use it extend it and add:
     * - Extend 'needs' to have parent object and wall-post list controllers.
     * - Overwrite 'parentId' to return the id of the parent object.
     * - Overwrite 'wallPostList' to return the array (model) that holds the wall-post list.
     * - Define a 'type'
     *
     * Look at App.ProjectTextWallPostNewController for example
     */

    init: function() {
        this._super();
        this.createNewWallPost();
    },

    createNewWallPost: function() {
        // Make sure we keep parent id/type
        var parentType = this.get('parentType');
        var parentId = this.get('parentId');

        this.set('model', App.TextWallPost.createRecord());

        this.set('parentType', parentType);
        this.set('parentId', parentId);
    },

    wallPostList: function(){
        return Em.K();
    }.property(),

    _wallPostSuccess: function (record) {
        var _this = this,
            list = _this.get('wallPostList');

        list.unshiftObject(record);
        Ember.run.next(function() {
            _this.createNewWallPost();
        });
    },

    _hideWallPostMessage: function() {
        $(".wallpost-message-area").hide();
    },

    actions: {
        saveWallPost: function() {
            var _this = this,
                parent_type = this.get('parentType'),
                parent_id = this.get('parentId'),
                wallPost = this.get('model');

            _this._hideWallPostMessage();

            if (parent_type && parent_id) {
                wallPost.set('parent_id', parent_id);
                wallPost.set('parent_type', parent_type);
            }
            wallPost.set('type', 'text');

            wallPost.save().then(function (record) {
                _this._wallPostSuccess(record);
            }, function (record) {
                _this.set('errors', record.get('errors'));
            });
        }
    }
});


App.MediaWallPostNewController = App.TextWallPostNewController.extend({

    // This a temporary container for App.Photo records until they are connected after this wall-post is saved.
    uploadFiles: Em.A(),

    createNewWallPost: function() {
        // Make sure we keep parent id/type
        var parentType = this.get('parentType');
        var parentId = this.get('parentId');

        this.set('model', App.MediaWallPost.createRecord());

        this.set('parentType', parentType);
        this.set('parentId', parentId);
    },

    _wallPostSuccess: function (record) {
        var _this = this;
        Ember.run.next(function() {
            if (_this.get('uploadFiles').length) {
                // Connect all photos to this wallpost.
                var reload = true;
                _this.get('uploadFiles').forEach(function(photo){
                    photo.set('mediawallpost', record);
                    photo.save();
                });
                // Empty this.files so we can use it again.
                _this.set('uploadFiles', Em.A());
            }
            var list = _this.get('wallPostList');
            list.unshiftObject(record);
            _this.createNewWallPost()
        });
    },
    actions: {
        addFile: function(file) {
            var store = this.get('store');
            var photo = store.createRecord(App.WallPostPhoto);
            // Connect the file to it. DRF2 Adapter will sort this out.
            photo.set('photo', file);
            photo.save();
            var controller = this;
            // Store the photo in this.files. We need to connect it to the wallpost later.
            photo.on('didCreate', function(record){
                controller.get('uploadFiles').pushObject(photo);
            });
        },

        removeFile: function(photo) {
            photo.deleteRecord();
            photo.save();
            // Remove it from temporary array too.
            this.get('uploadFiles').removeObject(photo);
        },

        showImages: function(event) {
            $(".photos-tab").addClass("active");
            $(".video-tab").removeClass("active");

            $(".video-container").hide();
            $(".photos-container").show();
        },

        showVideo: function() {
            $(".photos-tab").removeClass("active");
            $(".video-tab").addClass("active");

            $(".video-container").show();
            $(".photos-container").hide();
        }
    }
});


/* Task WallPosts */

App.TaskWallPostMixin = Em.Mixin.create({
    needs: ['task', 'taskIndex'],
    type: 'task',

    parentId: function(){
        return this.get('controllers.task.model.id');
    }.property('controllers.task.model.id'),

    wallPostList: function(){
        return this.get('controllers.task.model');
    }.property('controllers.task.model')

});

App.TaskTextWallPostNewController = App.TextWallPostNewController.extend(App.TaskWallPostMixin, {});
App.TaskMediaWallPostNewController = App.MediaWallPostNewController.extend(App.TaskWallPostMixin, {});


/* Project WallPosts */

App.ProjectWallPostMixin = Em.Mixin.create({

    needs: ['project', 'projectIndex'],
    type: 'project',

    parentId: function(){
        return this.get('controllers.project.model.id');
    }.property('controllers.project.model.id'),

    wallPostList: function(){
        return this.get('controllers.projectIndex.model');
    }.property('controllers.projectIndex.model')
});

App.ProjectTextWallPostNewController = App.TextWallPostNewController.extend(App.ProjectWallPostMixin, {});
App.ProjectMediaWallPostNewController = App.MediaWallPostNewController.extend(App.ProjectWallPostMixin, {});


/* FundRaiser WallPosts */

App.FundRaiserWallPostMixin = Em.Mixin.create({

    needs: ['fundRaiser', 'fundRaiserIndex'],
    type: 'fundraiser',
    parentType: 'fundraiser',

    parentId: function(){
        return this.get('controllers.fundRaiser.model.id');
    }.property('controllers.fundRaiser.model.id'),

    wallPostList: function(){
        return this.get('controllers.fundRaiserIndex.model');
    }.property('controllers.fundRaiserIndex.model')
});

App.FundRaiserTextWallPostNewController = App.TextWallPostNewController.extend(App.FundRaiserWallPostMixin, {});
App.FundRaiserMediaWallPostNewController = App.MediaWallPostNewController.extend(App.FundRaiserWallPostMixin, {});


/* Reactions */

App.WallPostReactionController = Em.ObjectController.extend(App.IsAuthorMixin, {});


App.WallPostReactionListController = Em.ArrayController.extend({
    init: function() {
        this._super();
        this.createNewReaction();
    },

    createNewReaction: function() {
        var store = this.get('store');
        var reaction =  store.createRecord(App.WallPostReaction);
        var name = this.get('currentUser.full_name');
        var values = {'name': name};
        var placeholder_unformatted = gettext("Hey %(name)s, you can leave a comment");
        var formatted_placeholder = interpolate(placeholder_unformatted, values, true);       
        reaction.set('placeholder', formatted_placeholder);
        this.set('newReaction', reaction);
    },

    addReaction: function() {
        var reaction = this.get('newReaction');
        // Set the wallpost that this reaction is related to.
        reaction.set('wallpost', this.get('target.model'));
        reaction.set('created', new Date());
        var controller = this;
        reaction.on('didCreate', function(record) {
            controller.createNewReaction();
            // remove is-selected from all input roms
            $('form.is-selected').removeClass('is-selected');
        });
        reaction.on('becameInvalid', function(record) {
            controller.createNewReaction();
            controller.set('errors', record.get('errors'));
            record.deleteRecord();
        });
        reaction.save();
    }
});
