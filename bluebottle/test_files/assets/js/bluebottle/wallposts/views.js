
/*
 Views
 */

App.MediaWallPostNewView = Em.View.extend({
    templateName: 'media_wallpost_new',
    tagName: 'form',

    submit: function(e) {
        e.preventDefault();
        this.get('controller').addMediaWallPost();
    },

    didInsertElement: function() {
        this.get('controller').clearWallPost();
    }
});


App.TextWallPostNewView = Em.View.extend({
    templateName: 'text_wallpost_new',
    tagName: 'form',

    submit: function(e){
        e.preventDefault();
        this.get('controller').addTextWallPost();
    },

    didInsertElement: function() {
        this.get('controller').clearWallPost();
    }
});


App.SystemWallPostView = Em.View.extend({
    templateName: 'system_wallpost'
});


App.ImportantWallPostView = Em.View.extend({
    templateName: 'important_wallpost'
});

App.ProjectWallPostView = Em.View.extend({
    templateName: 'project_wallpost',

    didInsertElement: function(){
        // Give it some time to really render...
        // Hack to make sure photo viewer works for new wallposts
        Em.run.later(function(){
            this.$('.photo-viewer a').colorbox({
                rel: this.toString(),
                next: '<span class="flaticon solid right-2"></span>',
                previous: '<span class="flaticon solid left-2"></span>',
                close: 'x'
            });
        }, 500);
    },

    actions: {
        deleteWallPost: function() {
            var view = this;
            var wallpost = this.get('controller.model');
            Bootstrap.ModalPane.popup({
                heading: gettext("Really?"),
                message: gettext("Are you sure you want to delete this comment?"),
                primary: gettext("Yes"),
                secondary: gettext("Cancel"),
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        view.$().fadeOut(500, function() {
                            wallpost.deleteRecord();
                            wallpost.save();
                        });
                    }
                }
            });
        }
    }

});


App.TaskWallPostView = App.ProjectWallPostView.extend({
    templateName: 'task_wallpost'

});

// This is the view toi display the wallpost list
// Idea of how to have child views with different templates:
// http://stackoverflow.com/questions/10216059/ember-collectionview-with-views-that-have-different-templates
App.ProjectIndexView = Em.View.extend({
    templateName: 'project_wallpost_list'
});


App.ProjectWallPostNewView = Em.View.extend({
    templateName: 'project_wallpost_new'
});


App.TaskWallPostListView = Em.View.extend({
    templateName: 'task_wallpost_list'

});


App.TaskWallPostNewView = Em.View.extend({
    templateName: 'task_wallpost_new'
});


/* Reactions */

App.WallPostReactionView = Em.View.extend({
    templateName: 'wallpost_reaction',
    //tagName: 'li',
    //classNames: ['reaction'],
    actions: {
        deleteReaction: function() {
            var view = this;
            var model = this.get('controller.model');
            Bootstrap.ModalPane.popup({
                heading: gettext("Really?"),
                message: gettext("Are you sure you want to delete this reaction?"),
                primary: gettext("Yes"),
                secondary: gettext("Cancel"),
                callback: function(opts, e) {
                    e.preventDefault();
                    if (opts.primary) {
                        view.$().fadeOut(500, function() {
                            model.deleteRecord();
                            model.save();
                        });
                    }
                }
            });
        }
    }
});


App.WallPostReactionListView = Em.View.extend({
    templateName: 'wallpost_reaction_list',

    submit: function(e) {
        e.preventDefault();
        this.get('controller').addReaction();
    },

    didInsertElement: function(e) {
        var view = this;
        view.$('textarea').focus(function(e) {
            view.$('.reaction-form').addClass('is-selected');
        }).blur(function(e) {
            if (!$(this).val()) {
                // textarea is empty or contains only white-space
                view.$('.reaction-form').removeClass('is-selected');
            }
        });
    }
});

