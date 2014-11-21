/**
 * write a comment component
 *
 */

App.BbTextWallpostNewComponent = Ember.Component.extend({
    id: "df",

    didInsertElement: function() {
        var el = $(Ember.get(this, 'element')),
            tab = Ember.get(this, 'tab'),
            _this = this, 
            textArea = this.$().find('textarea'),
            video = this.$().find('#wallpost-video'),
            photo = this.$().find('#wallpost-photo');

        el.find('li:first').addClass('active');

        el.find('li:gt(0)').each(function(){
            tab.apply(_this, [$(this)]).hide();
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

        textArea.on('focus', function() {
            _this.showWallpostOptions();
        });

        textArea.on('blur', function() {
            _this.hideWallpostOptions();
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

    tab: function(li){
        var el = this.$('.wallpost-update');
        return el.find('.tab:eq(' + li.index() + ')');
    },

    click: function(e){
        var el = this.$('.wallpost-update'),
            li = $(e.target).parent(),
            tab = Ember.get(this, 'tab');

        if(li.is('li')) {
            tab.apply(this, [el.find('.active').removeClass('active')]).hide();
            tab.apply(this, [li.addClass('active')]).show();
        }
    },

    actions: {
        submit: function() {
            this.sendAction("submit");
        }
    }
});

App.BbMediaWallpostNewComponent = App.BbTextWallpostNewComponent.extend();


