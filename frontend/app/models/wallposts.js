/**
 * Embedded mapping
 */

App.Adapter.map('App.Wallpost', {
    author: {embedded: 'load'},
    photos: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.TextWallpost', {
    author: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.MediaWallpost', {
    author: {embedded: 'load'},
    photos: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.WallpostReaction', {
    author: {embedded: 'load'}
});


/*
 Models
 */


App.WallpostPhoto = DS.Model.extend({
    url: 'wallposts/photos',
    photo: DS.attr('image'),
    mediawallpost: DS.belongsTo('App.MediaWallpost')
});

// This is union of all different wallposts.
App.Wallpost = DS.Model.extend({
    url: 'wallposts',

    // Model fields
    author: DS.belongsTo('App.UserPreview'),
    title: DS.attr('string', {defaultValue: ''}),
    text: DS.attr('string', {defaultValue: ''}),
    type: DS.attr('string'),
    created: DS.attr('date'),
    reactions: DS.hasMany('App.WallpostReaction'),
    email_followers: DS.attr('boolean'),

    video_url: DS.attr('string', {defaultValue: ''}),
    video_html: DS.attr('string'),
    photos: DS.hasMany('App.WallpostPhoto'),

    parent_id: DS.attr('string'),
    parent_type: DS.attr('string'),

    related_id: DS.attr('string'),
    related_type: DS.attr('string'),

    related_object: DS.attr('object'), // keep it generic

    isSystemWallpost: function(){
        return (this.get('type') == 'system');
    }.property('type'),

    // determine if this wallpost is related to a fundraiser
    fundraiser: function() {
        if (this.get('related_object')){
            var fundraiser = this.get('related_object').fundraiser;
            if(this.get('isSystemWallpost') && this.get('related_type') == 'donation' && fundraiser !== undefined){
                return fundraiser;
            }
        }
        return false;
    }.property('related_type', 'isSystemWallpost', 'related_object'),
	
	coverPhoto: function() {
		return this.get("photos").toArray()[0];
	}.property("photos"),
	
	otherPhotos: function() {
		var photos = this.get("photos").toArray();
		return photos.slice(1,photos.length);
	}.property("photos"),

    isInitiator: function(){
        return (this.get('type') == 'media');
    }.property('type')
});


App.TextWallpost = App.Wallpost.extend({
    url: 'wallposts/textwallposts'
});


App.MediaWallpost = App.Wallpost.extend({
    url: 'wallposts/mediawallposts'
});


/* Reactions */


App.WallpostReaction = DS.Model.extend({
    url: 'wallposts/reactions',

    text: DS.attr('string'),
    author: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date'),
    wallpost: DS.belongsTo('App.Wallpost')
});

