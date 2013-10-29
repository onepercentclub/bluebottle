/**
 * Embedded mapping
 */

App.Adapter.map('App.WallPost', {
    author: {embedded: 'load'},
    photos: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.ProjectWallPost', {
    author: {embedded: 'load'},
    photos: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.ProjectTextWallPost', {
    author: {embedded: 'load'},
    photos: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.ProjectMediaWallPost', {
    author: {embedded: 'load'},
    photos: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.TaskWallPost', {
    author: {embedded: 'load'},
    reactions: {embedded: 'load'}
});
App.Adapter.map('App.WallPostReaction', {
    author: {embedded: 'load'}
});


/*
 Models
 */

App.ProjectWallPostPhoto = DS.Model.extend({
    url: 'projects/wallposts/media/photos',
    photo: DS.attr('image'),
    mediawallpost: DS.belongsTo('App.ProjectWallPost')
});



// This is union of all different wallposts.
App.WallPost = DS.Model.extend({
    url: 'wallposts',

    // Model fields
    author: DS.belongsTo('App.UserPreview'),
    title: DS.attr('string'),
    text: DS.attr('string'),
    type: DS.attr('string'),
    created: DS.attr('date'),
    reactions: DS.hasMany('App.WallPostReaction'),

    video_url: DS.attr('string'),
    video_html: DS.attr('string'),
    photos: DS.hasMany('App.ProjectWallPostPhoto'),

    isSystemWallPost: function(){
        return (this.get('type') == 'system');
    }.property('type')
});


App.ProjectWallPost = App.WallPost.extend({
    url: 'projects/wallposts',
    project: DS.belongsTo('App.Project')
});


App.NewProjectWallPost = App.ProjectWallPost.extend({
    url: 'projects/wallposts'
});

App.ProjectMediaWallPost = App.ProjectWallPost.extend({
    url: 'projects/wallposts/media'
});

App.ProjectTextWallPost = App.ProjectWallPost.extend({
    url: 'projects/wallposts/text'
});


App.TaskWallPost = App.WallPost.extend({
    url: 'tasks/wallposts',
    task: DS.belongsTo('App.Task')
});


/* Reactions */


App.WallPostReaction = DS.Model.extend({
    url: 'wallposts/reactions',

    text: DS.attr('string'),
    author: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date'),
    wallpost: DS.belongsTo('App.WallPost')
});

