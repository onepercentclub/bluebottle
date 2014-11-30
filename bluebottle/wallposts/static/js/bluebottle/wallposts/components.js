/**
 * write a comment component
 *
 */

App.BbTextWallpostNewComponent = Ember.Component.extend({
    id: "df",

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

    showWallpostOptions: function() {
        var wallpost = this.$().find('.wallpost-update');
        wallpost.addClass('is-active');
    },

    hideWallpostOptions: function() {
        var wallpost = this.$().find('.wallpost-update');
        wallpost.removeClass('is-active');
    },

    actions: {
        submit: function() {
            this.sendAction("submit");
        }
    }
});

App.BbMediaWallpostNewComponent = App.BbTextWallpostNewComponent.extend({
    actions: {
        addFile: function(file){
            this.sendAction('addFile', file);
        },
        removeFile: function(file){
            this.sendAction('removeFile', file);
        }
    }

});


