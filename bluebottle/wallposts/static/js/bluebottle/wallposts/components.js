/**
 * Wallpost & comment components
 *
 */

App.FormControls = Ember.Mixin.create({
    showWallpostOptions: function(elm) {
        var element = this.$(elm);
        element.addClass('is-active');
    },

    hideWallpostOptions: function(elm) {
        var element = this.$(elm);
        element.removeClass('is-active');
    }
});

App.BbTextWallpostNewComponent = Ember.Component.extend(App.FormControls, {
    /**
     * This is the base component for a wall-post form.
     *
     */
    tagName: 'form',
    elementId: 'wallpost-form',

    translatables: {
        leaveCommentText: gettext('Leave a comment for this campaign')
    },

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

        textArea.on('focus', function() {
            _this.showWallpostOptions('.wallpost-update');
        });
    },

    actions: {
        close: function() {
            this.sendAction('close');
        },
        clearForm: function(){
            this.hideWallpostOptions('.wallpost-update');
        },

        saveWallpost: function() {
            var _this = this,
                wallpost = this.get('wallpost');

            wallpost.on('didCreate', function(record){
                _this._wallpostSuccess(record);
            });
            wallpost.on('becameError', function(record){
                _this._wallpostError(record);
            });

            _this.hideWallpostOptions('.wallpost-update');

            this.sendAction('addWallpost', wallpost);
        }
    }
});

App.BbModalTextWallpostNewComponent = App.BbTextWallpostNewComponent.extend({
    elementId: 'wallpost-success-form',
    needs: ['project', 'fundraiser'],

    translatables: {
        shoutoutText: gettext('Give a shout-out to the campaigner!')
    },

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
        },

        close: function() {
            this.sendAction('close');
        }
    }
});

App.BbMediaWallpostNewComponent = App.BbTextWallpostNewComponent.extend({
    translatables: {
        shareText: gettext('Share an update with your supporters'),
        videoText: gettext('Youtube or Vimeo url')
    },

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
            _this.showWallpostOptions('.wallpost-update');
        });

        $('.wallpost-update .action-cancel').on('click', function() {
            // TODO: Reset textareas and linked images?
            _this.hideWallpostOptions('.wallpost-update');
        });


        photo.on('change', function() {
            if (photo.val() === '') {
                _this.hideWallpostOptions('.wallpost-update');
            } else {
                _this.showWallpostOptions('.wallpost-update');
            }
        });

        video.on('keyup', function() {
            if (video.val() === '') {
                _this.hideWallpostOptions('.wallpost-update');
            } else {
                _this.showWallpostOptions('.wallpost-update');
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
    isAuthor: function () {
        var username = this.get('currentUser.username');
        var authorname = this.get('wallpost.author.username');
        if (username) {
            return (username == authorname);
        }
        return false;
    }.property('wallpost.author.username', 'currentUser.username'),

    actions: {
        removeWallpost: function(wallpost) {
            var _this = this,
                wallpost = this.get('wallpost');
            Bootstrap.ModalPane.popup({
                heading: gettext("Really?"),
                message: gettext("Are you sure you want to delete this post?"),
                primary: gettext("Yes"),
                secondary: gettext("Cancel"),
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        _this.$().fadeOut(500, function () {
                           _this.sendAction('removeWallpost', wallpost);
                        });
                    }
                }
            });
        },
        removeWallpostComment: function(comment) {
            this.sendAction('removeWallpostComment', comment);
        },
        addWallpostComment: function(comment) {
            this.sendAction('addWallpostComment', comment);
        },
        showProfile: function(profile) {
            this.sendAction('showProfile', profile);
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
            var _this = this,
                comment = this.get('comment');
            Bootstrap.ModalPane.popup({
                heading: gettext("Really?"),
                message: gettext("Are you sure you want to delete this comment?"),
                primary: gettext("Yes"),
                secondary: gettext("Cancel"),
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        _this.$().fadeOut(500, function () {
                            _this.sendAction('removeWallpostComment', comment);
                        });
                    }
                }
            });
        },

        showProfile: function(profile) {
            this.sendAction('showProfile', profile);
        }
    }
});

App.BbSystemWallpostComponent = App.BbWallpostComponent.extend({
    actions: {
        showProfile: function(profile) {
            this.sendAction('showProfile', profile);
        }
    }
})

App.BbWallpostCommentListComponent = Em.Component.extend(App.FormControls, {
    firstName: function() {
        var firstName = this.get('currentUser.first_name');
        return gettext('Leave a comment, ') + firstName;
    }.property(),

    init: function() {
        this._super();
        this.createNewComment();
    },

    didInsertElement: function() {
        var textArea = this.$().find('textarea'),
            _this = this;

        textArea.on('focus', function() {
            _this.showWallpostOptions('.m-comment-form');
        });

        $('.m-comment-form .action-cancel').on('click', function() {
            _this.hideWallpostOptions('.m-comment-form');
        });
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
            comment.set('wallpost', this.get('wallpost'));
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
            _this.hideWallpostOptions('.m-comment-form');
            _this.sendAction('addWallpostComment', comment);
        },
        removeWallpostComment: function(comment){
            this.sendAction('removeWallpostComment', comment);
        },
        showProfile: function(profile) {
            this.sendAction('showProfile', profile);
        }
    }
});
