/**
 * Wallpost & comment components
 *
 */

App.BbTextWallpostNewComponent = Ember.Component.extend({
    /**
     * This is the base component for a wall-post form.
     *
     */
    tagName: 'form',
    elementId: 'wallpost-form',

    _wallpostSuccess: function(){
    },

    _wallpostError: function(){
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
        var wallpost = this.$('.wallpost-update');
        wallpost.addClass('is-active');
    },

    hideWallpostOptions: function() {
        var wallpost = this.$('.wallpost-update');
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
                _this._wallpostError(record);
            });
            this.sendAction('addWallpost', wallpost);
        }
    }
});

App.BbModalTextWallpostNewComponent = App.BbTextWallpostNewComponent.extend({

    needs: ['project', 'fundraiser'],

    _wallpostSuccess: function (record) {
        // Close modal
        this.sendAction('close');
    },
    _hideWallpostMEssage: function (){
        this.$(".wallpost-message-area").hide();
    },

    init: function() {
        this._super();
        this.createNewWallpost();
    },

    createNewWallpost: function() {
        // Make sure we keep parent id/type
        var parentType = this.get('parentType');
        var parentId = this.get('parentId');

        this.set('wallpost', App.TextWallPost.createRecord({
            parent_type: parentType,
            parent_id: parentId,
            type: 'text'
        }));
    },

    textLengthMax: 140,
    textLength: function(){
        return this.get('wallpost.text').length;
    }.property('wallpost.text'),

    actions: {
        addWallpost: function () {
            var _this = this
                parent_type = this.get('parentType'),
                parent_id = this.get('parentId'),
                wallpost = this.get('wallpost');

            _this.sendAction('close');
            _this.sendAction('addWallpost', wallpost);
        }
    }
});

App.BbMediaWallpostNewComponent = App.BbTextWallpostNewComponent.extend({

    didInsertElement: function() {
        var _this = this,
            textArea = this.$().find('textarea'),
            video = this.$().find('#wallpost-video'),
            photo = this.$().find('#wallpost-photo');

        $('.wallpost-update .action-add-photo').on('click', function() {
            $(this).toggleClass('is-active');
            $('.wallpost-photos').toggleClass('is-active');
        });

        $('.wallpost-update .action-add-video').on('click', function() {
            $(this).toggleClass('is-active');
            $('.wallpost-video').toggleClass('is-active');
        });

        textArea.on('focus', function() {
            _this.showWallpostOptions();
        });

        $('.wallpost-update .action-cancel').on('click', function() {
            // TODO: Reset textareas and linked images?
            _this.hideWallpostOptions();
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
        addFile: function(file) {
            this.sendAction('addFile', file);
        },

        removeFile: function(file) {
            this.sendAction('removeFile', file);
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
        removeWallpost: function(wallpost) {
            this.sendAction('removeWallpost', wallpost);
        },
        removeWallpostComment: function(comment) {
            this.sendAction('removeWallpostComment', comment);
        },
        addWallpostComment: function(comment) {
            this.sendAction('addWallpostComment', comment);
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
    }
});


App.BbWallpostCommentComponent = Em.Component.extend({
    isAuthor: function () {
        var username = this.get('currentUser.username');
        var authorname = this.get('comment.author.username');
        if (username) {
            return (username == authorname);
        }
        return false;
    }.property('comment.author.username', 'currentUser.username'),

    actions: {
        removeWallpostComment: function (comment) {
            this.sendAction('removeWallpostComment', comment);
        }
    }
});


App.BbWallpostCommentListComponent = Em.Component.extend({
    init: function() {
        this._super();
        this.createNewComment();
    },

    createNewComment: function() {
        var comment =  App.WallPostReaction.createRecord();
        var name = this.get('currentUser.full_name');
        var values = {'name': name};
        var placeholder_unformatted = gettext("Hey %(name)s, you can leave a comment");
        var formatted_placeholder = interpolate(placeholder_unformatted, values, true);
        comment.set('placeholder', formatted_placeholder);
        this.set('newComment', comment);
    },

    actions: {
        addWallpostComment: function () {
            var _this = this,
                comment = this.get('newComment');
            // Set the wallpost that this comment is related to.
            comment.set('wallpost', this.get('post'));
            comment.set('created', new Date());
            var controller = this;
            comment.on('didCreate', function (record) {
                // Successfully saved comment
                // remove is-selected from input form
                _this.$('form.is-selected').removeClass('is-selected');
                _this.createNewComment();
            });
            comment.on('becameInvalid', function (record) {
                // Error saving Comment
            });
            _this.sendAction('addWallpostComment', comment);
        },
        removeWallpostComment: function(comment){

        }
    }
});
