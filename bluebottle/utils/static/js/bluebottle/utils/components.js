App.BbFlashComponent = Em.Component.extend({
    tagName: ''
});

App.BbFormFieldComponent = Em.Component.extend({

});

App.BbTextFieldComponent = App.BbFormFieldComponent.extend({
    type: 'text'
});

App.BbTextAreaComponent = App.BbFormFieldComponent.extend({

  didInsertElement: function(){
    var el = this.$('textarea.redactor');
    var view = this;
    $(el).redactor({
        buttons: ['formatting', 'bold', 'italic', 'deleted', 'unorderedlist', 'orderedlist', 'link', 'horizontalrule'],
        minHeight: 350,
        blurCallback: function(e){
            $(el).val(view.$('.redactor').redactor('get'));
            $(el).trigger('change');
        }
    });
    $(el).redactor('insertHtml', view.get('value'));
  }
});

App.BbMapPickerComponent = App.BbFormFieldComponent.extend({
});

App.BbDatePickerComponent = App.BbFormFieldComponent.extend({
});

App.BbDatePickerSliderComponent = App.BbFormFieldComponent.extend({
});



App.BbUploadImageComponent = App.BbFormFieldComponent.extend({
    accept: 'image/*',
    buttonLabel: 'Upload image'
});


App.BbUploadMultipleImagesComponent = Ember.Component.extend({
    actions: {
        addFile: function(file){
            this.sendAction('addFile', file);
        },
        removeFile: function(file){
            this.sendAction('removeFile', file);
        }
    }
});


App.BbUploadImageAreaComponent = App.BbFormFieldComponent.extend({
    accept: 'image/*',
    buttonLabel: 'Upload image',
    didInsertElement: function() {
    	var file_input = this.$("input[type=file]");
    	file_input.hide();
    	this.$(".image-upload-controls-browse").click(function() {
    		file_input.trigger("click");
    	});
    }
});

App.BbUploadFileAreaComponent = App.BbFormFieldComponent.extend({
    accept: '*/*',
    buttonLabel: 'Upload file',
    didInsertElement: function() {
    	var file_input = this.$("input[type=file]");
    	file_input.hide();
    	this.$(".upload").click(function() {
    		file_input.trigger("click");
    	});
    }
});

App.BbVideoLinkComponent = App.BbTextFieldComponent.extend({
});

App.BbRadioComponent = App.BbFormFieldComponent.extend({
    type: 'radio'
});

App.BbSelectComponent = App.BbFormFieldComponent.extend({

});


App.BbCopyCodeComponent = Ember.Component.extend({

    didInsertElement: function () {
        var controller = this.get('parentView.controller'),
            _this = this,
            clip = new ZeroClipboard(_this.$('.copy-to-clipboard'));
        clip.on('copy', function (client, args) {
            controller.send('closeModal');
            controller.send('setFlash', gettext("Copied!"));
        });
    }
});


App.BbVideoMainComponent = Em.Component.extend({
    errorCallback: function(message) {
         console.log(message);
    },

    playVideo: function(elm) {
        elm.api("play");
    },

    pauseVideo: function(elm) {
        elm.api("pause");
    },

    didInsertElement: function() {
        var customData = this.$().find('.video-item'),
            now = new Date().getTime(),
            options = {
                vimeo_number: this.vimeo_id || this.errorCallback('no vimeo number defined in options, please add this.'),
                background: this.backgroundImage || this.errorCallback('no video still defined in options, please add this.'),
                vimeo_color: this.vimeoColor || '009fe3',
                video_id: this.video_id || 'computed_id_' + now
            },
            _this = this,
            iframe = this.$().find('iframe'),
            setId = iframe.attr('id', options.video_id),
            setSrc = iframe.attr('src', '//player.vimeo.com/video/' + 
                        options.vimeo_number + '/?api=1&player_id='+ options.video_id + 
                        '&title=0&amp;byline=0&amp;portrait=0&amp;color=' + options.vimeo_color + ''),
            player = $f(iframe),
            animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
            videoItemContent = this.$().find('.video-item-content'),
            videoItem = this.$().find('.video-item');

        this.$().find('.video-item-content').css({'background-image': "url('" + options.background + "')"});

        this.$().find('.video-play-btn').on('mouseenter', function(){
            videoItemContent.addClass("is-blur");
        });

        this.$().find('.video-play-btn').on('mouseleave', function(){
            videoItemContent.removeClass("is-blur");
        });

        this.$().find('.video-play-btn').on('click', function(){
            videoItem.removeClass("is-inactive");
            videoItem.addClass("is-active");
            // unsliderData.stop();
            _this.playVideo(player);
        });

        this.$().find('.close-video').on('click', function(){
            videoItem.removeClass("is-active");
            videoItem.addClass("is-inactive");
            _this.pauseVideo(player);

            $('.video-item').one(animationEnd, function(){
                videoItem.removeClass("is-inactive");
            });
        });

        function onFinish(id) {
            videoItem.removeClass("is-active");
            videoItem.addClass("is-inactive");

            $('.video-item').one(animationEnd, function(){
                videoItem.removeClass("is-inactive");
                // unsliderData.start();
            });
        }
        
        function onPlayProgress(data, id) {
            // unsliderData.stop();
        }
        
        player.addEvent('ready', function() {
            player.addEvent('finish', onFinish);
            player.addEvent('playProgress', onPlayProgress);
        });
    }
});

