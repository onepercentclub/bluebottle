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


