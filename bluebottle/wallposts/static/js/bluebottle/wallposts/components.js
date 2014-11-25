/**
 * Wallpost & comment components
 *
 */


App.BbTextWallpostNewComponent = Ember.Component.extend({
    /**
     * This is the base class for a wall-post form.
     *
     * To use it extend it and add:
     * - Extend 'needs' to have parent object and wall-post list controllers.
     * - Overwrite 'parentId' to return the id of the parent object.
     * - Overwrite 'wallpostList' to return the array (model) that holds the wall-post list.
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

        this.set('wallpost', App.TextWallPost.createRecord());

        this.set('parentType', parentType);
        this.set('parentId', parentId);
    },

    _wallpostSuccess: function (record) {
        var _this = this,
            list = _this.get('wallpostList');

        list.unshiftObject(record);
        Ember.run.next(function() {
            _this.createNewWallPost();
        });
    },

    _hideWallpostMessage: function() {
        $(".wallpost-message-area").hide();
    },

    didInsertElement: function() {
        var _this = this, 
            textArea = this.$().find('textarea');

        textArea.on('keyup', function() {
            if (textArea.val().length > 0) {
                _this.showWallpostOptions();
            } else {
                _this.hideWallpostOptions();
            }
        });
    },

    showWallpostOptions: function() {
        var wallpost = this.$().find('.wallpost-update');
        wallpost.addClass('is-active');
    },

    hideWallpostOptions: function() {
        var wallpost = this.$().find('.wallpost-update');
        wallpost.removeClass('is-active');
    },

    actions: {
        clearForm: function(){
            this.createNewWallPost();
            this._hideWallpostMessage();
        },
        saveWallpost: function() {
            var _this = this,
                parent_type = this.get('parentType'),
                parent_id = this.get('parentId'),
                wallpost = this.get('wallpost');

            _this._hideWallpostMessage();

            if (parent_type && parent_id) {
                wallpost.set('parent_id', parent_id);
                wallpost.set('parent_type', parent_type);
            }
            wallpost.set('type', 'text');

            wallpost.save().then(function (record) {
                _this._wallpostSuccess(record);
            }, function (record) {
                _this.set('errors', record.get('errors'));
            });
        }
    }
});

App.BbMediaWallpostNewComponent = App.BbTextWallpostNewComponent.extend({

    uploadFiles: Em.A(),

    createNewWallPost: function() {
        // Make sure we keep parent id/type
        var parentType = this.get('parentType');
        var parentId = this.get('parentId');

        this.set('wallpost', App.MediaWallPost.createRecord());

        this.set('parentType', parentType);
        this.set('parentId', parentId);
    },

    _wallpostSuccess: function (record) {
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
            var list = _this.get('wallpostList');
            list.unshiftObject(record);
            _this.createNewWallPost()
        });
    },

    didInsertElement: function() {
        var _this = this,
            textArea = this.$().find('textarea'),
            video = this.$().find('#wallpost-video'),
            photo = this.$().find('#wallpost-photo');

        $('.add-photo a').on('click', function() {
            $(this).parent('li').toggleClass('is-active');
            $('.photo').toggleClass('is-active');
        });

        $('.add-video a').on('click', function() {
            $(this).parent('li').toggleClass('is-active');
            $('.vid').toggleClass('is-active');
        });

        textArea.on('keyup', function() {
            if (textArea.val().length > 0) {
                _this.showWallpostOptions();
            } else {
                _this.hideWallpostOptions();
            }
        });

        photo.on('change', function() {
            if (photo.val() === '') {
                _this.hideWallpostOptions();
            } else {
                _this.showWallpostOptions();
            }
        });

        video.on('keyup', function() {
            if (video.val() === '') {
                _this.hideWallpostOptions();
            } else {
                _this.showWallpostOptions();
            }
        });
    },

    actions: {
        saveWallpost: function() {
            var _this = this,
                parent_type = this.get('parentType'),
                parent_id = this.get('parentId'),
                wallpost = this.get('wallpost');

            _this._hideWallPostMessage();

            if (parent_type && parent_id) {
                wallpost.set('parent_id', parent_id);
                wallpost.set('parent_type', parent_type);
            }
            wallpost.set('type', 'text');

            wallpost.save().then(function (record) {
                _this._wallpostSuccess(record);
            }, function (record) {
                _this.set('errors', record.get('errors'));
            });
        },
        clearForm: function(){
            this.createNewWallPost();
        },
        addFile: function(file) {
            var photo = App.WallPostPhoto.createRecord();
            photo.set('photo', file);
            photo.save();
            var _this = this;
            // Store the photo in this.files. We need to connect it to the wallpost later.
            photo.on('didCreate', function(record){
                _this.get('uploadFiles').pushObject(photo);
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


App.BbWallpostComponent = Em.Component.extend({
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


App.WallpostCommentComponent = Em.Component.extend(App.IsAuthorMixin, {});


App.BbWallpostReactionListComponent = Em.Component.extend({
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
        reaction.set('wallpost', this.get('target.post'));
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
