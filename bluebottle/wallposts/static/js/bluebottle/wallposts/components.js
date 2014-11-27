/**
 * Wallpost & comment components
 *
 */

App.BbWallpostListComponent = Ember.Component.extend({

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

    actions: {
        showMoreWallposts: function(){
            this.sendAction('showMoreWallposts');
        },
        addWallpost: function(wallpost){
            this.sendAction('addWallpost', wallpost);
        },
        removeWallpost: function(wallpost){
            this.sendAction('removeWallpost', wallpost);
        }
    }
});


App.BbTextWallpostNewComponent = Ember.Component.extend({
    /**
     * This is the base component for a wall-post form.
     *
     */
    tagName: 'form',
    elementId: 'wallpost-form',


    init: function() {
        this._super();
        this.createNewWallpost();
    },

    createNewWallpost: function() {

        var parentType = this.get('parentType');
        var parentId = this.get('parentId');

        this.set('wallpost', App.TextWallPost.createRecord({
            type: 'text',
            parent_type: parentType,
            parent_id: parentId
        }));
    },

    _wallpostSuccess: function (record) {
        var _this = this,
            list = _this.get('wallpostList');

        list.unshiftObject(record);
        Ember.run.next(function() {
            _this.createNewWallpost();
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
            this.createNewWallpost();
            this.hideWallpostOptions();
        },
        saveWallpost: function() {
            var _this = this,
                wallpost = this.get('wallpost');

            _this._hideWallpostMessage();

            wallpost.on('didCreate', function(record){
                _this._wallpostSuccess(record);
            });
            wallpost.on('becameError', function(record){
                _this.set('errors', record.get('errors'));
            });
            this.sendAction('addWallpost', wallpost);
        }
    }
});

App.BbModalTextWallpostNewComponent = App.BbTextWallpostNewComponent.extend({
    _wallpostSuccess: function (record) {
        var list = this.get('wallpostList');

        // Close modal
        this.sendAction('close');

        // Add new wallpost to list (if one was specified).
        if (list) list.unshiftObject(record);
    },
    _hideWallpostMEssage: function (){
        this.$(".wallpost-message-area").hide();
    },
    textLengthMax: 140,
    textLength: function(){
        return this.get('wallpost.text').length;
    }.property('wallpost.text'),

    actions: {
        clearForm: function(){
            this.createNewWallpost();
            this.hideWallpostOptions();
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

    createNewWallpost: function() {
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
            _this.createNewWallpost()
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
        },
        clearForm: function(){
            this.hideWallpostOptions();
            this.createNewWallpost();
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
    },
    didInsertElement: function(){
        var view = this;
        view.$().hide();
        // Give it some time to really render...
        // Hack to make sure photo viewer works for new wallposts
        Em.run.next(function(){

            // slideDown has weird behaviour on Task Wall with post not appearing.
            // view.$().slideDown(500);
            view.$().fadeIn(500);

            view.$('.photo-viewer a').colorbox({
                rel: this.toString(),
                next: '<span class="flaticon solid right-2"></span>',
                previous: '<span class="flaticon solid left-2"></span>',
                close: 'x'
            });
        });
    },


});


App.WallpostCommentComponent = Em.Component.extend(App.IsAuthorMixin, {});


App.BbWallpostCommentListComponent = Em.Component.extend({
    init: function() {
        this._super();
        this.createNewReaction();
    },

    createNewReaction: function() {
        var reaction =  App.WallPostReaction.createRecord();
        var name = this.get('currentUser.full_name');
        var values = {'name': name};
        var placeholder_unformatted = gettext("Hey %(name)s, you can leave a comment");
        var formatted_placeholder = interpolate(placeholder_unformatted, values, true);
        reaction.set('placeholder', formatted_placeholder);
        this.set('newReaction', reaction);
    },

    actions: {
        addReaction: function () {
            var reaction = this.get('newReaction');
            // Set the wallpost that this reaction is related to.
            reaction.set('wallpost', this.get('post'));
            reaction.set('created', new Date());
            var controller = this;
            reaction.on('didCreate', function (record) {
                controller.createNewReaction();
                // remove is-selected from all input roms
                $('form.is-selected').removeClass('is-selected');
            });
            reaction.on('becameInvalid', function (record) {
                controller.createNewReaction();
                controller.set('errors', record.get('errors'));
                record.deleteRecord();
            });
            reaction.save();
        }
    }
});
