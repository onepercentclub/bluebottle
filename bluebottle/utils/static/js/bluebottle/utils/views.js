App.TagField = Em.TextField.extend({
    keyUp: function(e){
        if (e.keyCode == 188) {
            e.preventDefault();
            var val = this.get('value');
            val = val.replace(',','');
            this.set('parentView.new_tag', val);
            this.get('parentView').addTag();
        }
    }
});

App.TagWidget = Em.View.extend({
    templateName: 'tag_widget',
    actions: {
        addTag: function(){
            if (this.get('new_tag')) {
                var new_tag = this.get('new_tag').toLowerCase();
                var tags = this.get('tags');
                // Try to create a new tag, it will fail if it's already in the local store, so catch that.
                try {
                    var tag = App.Tag.createRecord({'id': new_tag});
                } catch(err) {
                    var tag = App.Tag.find(new_tag);
                }
                tag.transitionTo('created.loaded.saved');
                tags.pushObject(tag);
                this.set('new_tag', '');
            }
        },
        removeTag: function(tag) {
            var tags = this.get('tags');
            tags.removeObject(tag);
        }
    },

    didInsertElement: function(){
        var $tag = this.$('.tag');
        if ($tag.length && typeof $tag.typeahead == 'function') {
          $tag.typeahead({
              source: function (query, process) {
                  return $.get('/api/metadata/tags/' + query, function (data) {
                      return process(data);
                  });
              }
          })
        }
    }
});


/**
 * Generic view to plug-in social sharing functionality anywhere in the app.
 * e.g. {{view App.SocialShareView classNames="your-styling-class-name"}}
 *
 * Gets the entire current URL to share, and if available, extra metadata from the API.
 *
 * @class SocialShareView
 * @namespace App
 * @extends Ember.View
 *
 * NOTE: maybe we should look into url shortening?
 */
App.SocialShareView = Em.View.extend({
    templateName: 'social_share',
    dialogW: 626,
    dialogH: 436,
    
    canShare: function () {
        return App.get('shareEnabled');
    }.property(),

    shareOptions: function() {
        // if no options are explictly configured, return default set
        var options = App.get('shareOptions');

        if(typeof options === "undefined") {
            return {facebook: true, twitter: true};
        }
        return options;
    }.property(),

    didInsertElement: function(){
        // Because ZeroClipboard requires user interaction we can't handle the copy link as an action.
        var controller = this.get('parentView.controller'),
            _this = this,
            project = this.get('context'),
            server = document.location.protocol + '://' + document.location.host,
            link = server + '/go/projects/'
            clip = new ZeroClipboard(_this.$('.copy'));
        clip.on('complete', function (client, args) {
            clip.setText(link);
            controller.send('setFlash', gettext("Copied!"));
        });
    },

    actions: {
        shareOnFacebook: function() {
            // context is the model object defined in the associated controller/route
            var meta_data = this.get('context.meta_data'),
                tracker = this.get('controller.tracker'),
                controller = this.get('controller');
            
            if(meta_data && meta_data.url){
                var currentLink = encodeURIComponent(meta_data.url);
            } else {
                console.log('meta data not found');
                var currentLink = encodeURIComponent(location.href);
            }

            if (tracker) {
                tracker.trackEvent("Share", {project: controller.get('model.title'), network: "Facebook"});
                tracker.peopleIncrement('facebook_shares');
            }

            this.showDialog('https://www.facebook.com/sharer/sharer.php?u=', currentLink, 'facebook');
        },

        shareOnTwitter: function() {
            var meta_data = this.get('context.meta_data'),
                // status: e.g. Women first in Botswana {{URL}} via @1percentclub'
                tracker = this.get('controller.tracker'),
                controller = this.get('controller');
                
            if(meta_data.url){
                var currentLink = encodeURIComponent(meta_data.url);
            } else {
                var currentLink = encodeURIComponent(location.href);
            }

            var status = meta_data.tweet.replace('{URL}', currentLink);

            if (tracker) {
                tracker.trackEvent("Share", {project: controller.get('model.title'), network: 'Twitter' });
                tracker.peopleIncrement('twitter_shares');
            }

            this.showDialog('https://twitter.com/home?status=', status, 'twitter');
        },
        shareOnFlyer: function() {
            var project = this.get('context'),
                controller = this.get('controller');
            controller.send('openInBox', 'shareFlyer', project, 'modalFront');
        },
        shareEmbedded: function() {
            var project = this.get('context'),
                controller = this.get('controller');
            controller.send('openInBox', 'shareEmbedded', project, 'modalFront');
        }
    },

    showDialog: function(shareUrl, urlArgs, type) {
        window.open(shareUrl + urlArgs, type + '-share-dialog', 'width=' + this.get('dialogW') + ',height=' + this.get('dialogH'));
    }
});



App.ShareEmbeddedController = Em.Controller.extend({

    embedCode: function(){
        var code = '<link rel="stylesheet" href="/static/assets/css/widget.css" media="screen" />' +
                   '<script type="text/javascript" src="/static/assets/js/widget.js"></script>' +
                   '<div class="widget-container" data-language="en" data-project="' +
                    this.controllerFor('project').get('model.id') +
                    '"></div>';
        return code;
    }.property()

});


// See/Use App.DatePicker
App.DatePickerValue = Ember.TextField.extend({
    type: 'hidden',
    valueBinding: "parentView.value"
});

// See/Use App.DatePicker
App.DatePickerWidget = Ember.TextField.extend({
    placeholderBinding: "parentView.placeholder",
    dateBinding: "parentView.value",
    configBinding: "parentView.config",

    didInsertElement: function(){
        var config = this.get('config');
        this.$().datepicker(config);
        this.$().datepicker('setDate', this.get('date'));
    },

    change: function(){
        this.set('date', this.$().datepicker('getDate'));
    }
});

App.DatePickerButtonWidget = Ember.View.extend({
    templateName: 'date_picker_button',
    dateBinding: "parentView.value",
    configBinding: "parentView.config",
    didInsertElement: function(){
        var config = this.get('config');
        var view = this;
        config.onSelect = function(date, dp){
            view.set('date', view.$('input').datepicker('getDate'));
        }
        this.$('input').datepicker(config);
        this.$('input').datepicker('setDate', this.get('date'));

    },
    actions: {
        showDatePicker: function(){
            this.$('input').datepicker('show');
        }
    }
});

// This renders a TextField with the localized date.
// On click it will use jQuery UI date picker dialog so the user can select a date.
// valueBinding should bind to a  DS.attr('date') property of an Ember model.
App.DatePicker = Ember.ContainerView.extend({
    init: function(){
        this._super();
        if (this.get("minDate") != undefined) {
            this.config.minDate = this.get("minDate");
        }
        if (this.get("maxDate") != undefined) {
            this.config.maxDate = this.get("maxDate");
        }
    },
    config: {changeMonth: true, changeYear: true, yearRange: "c-100:c+10"},
    childViews: [App.DatePickerValue, App.DatePickerWidget]
});

App.DateSliderWidget = Ember.TextField.extend({
    type: 'range',
    dateBinding: "parentView.value",
    configBinding: "parentView.config",
    didInsertElement: function(){
        var config = this.get('config');
        var view = this;
        config.callback = function(days){
            var date = new Date(Date.now() + days * 24*3600*1000);
            view.set('date', date);
        },
        config.dimension = gettext('&nbsp;days');
        config.scale = [0, 100],
        config.limits = false,
        config.className = 'slider';
        this.$().slider(config);
        this.updateSlider();
    },
    updateSlider: function(){
        var date = this.get('date');
        if (date) {
            var now = new Date();
            var microseconds = date.getTime() - now.getTime();
            var days =  Math.ceil(microseconds / (1000 * 60 * 60 * 24));
            this.set('value', days);
            this.$().slider('value', days);
        }
    }.observes('date')
});


// This renders a slider and datepicker button.
// The slider counts in days. minDate and maxDate should be formated as '+30d'.
App.DatePickerSlider = Ember.ContainerView.extend({
    config: {minDate: 0, maxDate: '+100d'},
    init: function(){
        this._super();
        if (this.get("minDate") != undefined) {
            this.config.minDate = this.get("minDate");
        }
        if (this.get("maxDate") != undefined) {
            this.config.maxDate = this.get("maxDate");
        }
        this.config.from = parseInt(this.config.minDate.replace(/[\+d]/g, ''));
        this.config.to = parseInt(this.config.maxDate.replace(/[\+d]/g, ''));
    },
    childViews: [App.DatePickerValue, App.DateSliderWidget, App.DatePickerButtonWidget]
});


App.CustomDatePicker = App.DatePicker.extend({
    init: function(){
        this._super();
        if (this.get("minDate") != undefined) {
            this.config.minDate = this.get("minDate");
        }
        if (this.get("maxDate") != undefined) {
            this.config.maxDate = this.get("maxDate");
        }
    }
});


App.UploadMultipleFilesInput = Ember.TextField.extend({
    type: 'file',
    attributeBindings: ['name', 'accept', 'multiple'],

    didInsertElement: function(){
        // Or maybe try: https://github.com/francois2metz/html5-formdata.
        var view = this.$();
        if (Em.isNone(File)) {
            $.getScript('//ajax.googleapis.com/ajax/libs/swfobject/2.2/swfobject.js').done(
                function(){
                    $.getScript('/static/assets/js/polyfills/FileReader/jquery.FileReader.min.js').done(
                        function(){
                            view.fileReader({filereader: '/static/assets/js/polyfills/FileReader/filereader.swf'});
                        }
                    );
                }
            );
        }
    },

    //contentBinding: 'parentView.parentView.controller.content',

    change: function(e) {
        //var controller = this.get('parentView.parentView.controller');
        var files = e.target.files;
        for (var i = 0; i < files.length; i++) {
            var reader = new FileReader(),
                file = files[i],
                _this = this;
            reader.readAsDataURL(file);

            _this.$().parents('form').find('.preview').attr('src', '/static/assets/images/loading.gif');
            reader.onload = function(e) {
                _this.$().parents('form').find('.preview').attr('src', e.target.result);
            };
            _this.get('parentView').send('addFile', file);
        }
    }
});

