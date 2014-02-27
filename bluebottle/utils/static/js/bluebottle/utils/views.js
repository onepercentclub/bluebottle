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
        this.$('.tag').typeahead({
            source: function (query, process) {
                return $.get('/api/metadata/tags/' + query, function (data) {
                    return process(data);
                });
            }
        })
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

    actions: {
        shareOnFacebook: function() {
            var meta_data = this.get('context').get('meta_data');
            if(meta_data.url){
                var currentLink = encodeURIComponent(meta_data.url);
            } else {
                var currentLink = encodeURIComponent(location.href);
            }
            this.showDialog('https://www.facebook.com/sharer/sharer.php?u=', currentLink, 'facebook');
        },

        shareOnTwitter: function() {
            var meta_data = this.get('context').get('meta_data');

            if(meta_data.url){
                var currentLink = encodeURIComponent(meta_data.url);
            } else {
                var currentLink = encodeURIComponent(location.href);
            }

            // status: e.g. Women first in Botswana {{URL}} via @1percentclub'
            var status = meta_data.tweet.replace('{URL}', currentLink);

            this.showDialog('https://twitter.com/home?status=', status, 'twitter');
        }
    },

    showDialog: function(shareUrl, urlArgs, type) {
        window.open(shareUrl + urlArgs, type + '-share-dialog', 'width=' + this.get('dialogW') + ',height=' + this.get('dialogH'));
    }
});
