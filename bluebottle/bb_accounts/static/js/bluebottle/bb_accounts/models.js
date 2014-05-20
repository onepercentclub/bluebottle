/*
 Models
 */

/*
  A data model representing a user.

  Interacts with following public API:

  User Detail (GET/PUT):   /users/profiles/<pk>
 */
App.User = DS.Model.extend({
    url: 'users/profiles',

    username: DS.attr('string'),
    // TODO: loose these in favour of short/full name
    first_name: DS.attr('string'),
    last_name: DS.attr('string'),

    full_name: DS.attr('string'),
    short_name: DS.attr('string'),


    about: DS.attr('string'),
    why: DS.attr('string'),
    time_available: DS.belongsTo('App.TimeAvailable'),
    location: DS.attr('string'),

    picture: DS.attr('image'),

    website: DS.attr('string'),
    facebook: DS.attr('string'),
    twitter: DS.attr('string'),
    skypename: DS.attr('string'),

    date_joined: DS.attr('date'),
    file: DS.attr('string'),

    skills: DS.hasMany('App.Skill'),

    // post-only fields (i.e. only used for user creation)
    email: DS.attr('string'),
    password: DS.attr('string'),

    favourite_countries: DS.hasMany("App.Country"),
    favourite_themes: DS.hasMany("App.Theme"),

    tags: DS.hasMany("App.Tag", {embedded: "always"}),

    themes_list: function() {
        var arr = [];
        this.get('favourite_themes').forEach(function (item, index, self) {
            arr.push(item.get('name'));
        });
        return arr.join(', ');
    }.property('favourite_themes.@each.name'),

    countries_list: function() {
        var arr = [];
        this.get('favourite_countries').forEach(function (item, index, self) {
            arr.push(item.get('name'));
        });
        return arr.join(', ');
    }.property('favourite_countries.@each.name'),

    skills_list: function() {
        var arr = [];
        this.get('skills').forEach(function (item, index, self) {
            arr.push(item.get('name'));
        });
        return arr.join(', ');
    }.property('skills.@each.name'),

    tags_list: function() {
        var arr = [];
        this.get('tags').forEach(function(item, index, self) {
            arr.push(item.get('id'));
        });
        return arr.join(', ');
    }.property('tags.@each.id'),

    getPicture: function() {
        if (this.get('picture')) {
            return this.get('picture.large')
        }
        return STATIC_URL + 'images/default-avatar.png'
    }.property('picture'),

    getAvatar: function(){
        if (this.get('picture')) {
            return this.get('picture.square')
        }
        return STATIC_URL + 'images/default-avatar.png'
    }.property('picture'),

    getName: function() {
        if (this.get('first_name')) {
            return this.get('first_name')
        }
        return this.get('username')
    }.property('first_name'),

    get_website: function() {
        if (this.get('website').substr(0,7) == 'http://') {
            return this.get('website').replace('http://', '');
        } else if ((this.get('website').substr(0,11) == 'http://www.')) {
            return this.get('website').replace('http://www.', '');
        } else {
			return this.get('website');
		}
    }.property('website'),

    user_since: function() {
        return Globalize.format(this.get('date_joined'), 'd');
    }.property('date_joined'),

    get_twitter: function() {
        return '//twitter.com/' + this.get('twitter');
    }.property('twitter'),

    get_facebook: function() {
        return '//www.facebook.com/' + this.get('facebook');
    }.property('facebook')
});



// TODO: split this of
App.User.reopen({
    user_statistics: DS.attr('object')
});


/*
 A data model representing a user's settings.

 Interacts with following authenticated user API.

 User settings Detail (GET/PUT):  /users/settings/<pk>
 */
// TODO: fix date issue
// http://stackoverflow.com/questions/15695809/what-is-the-best-way-to-modify-the-date-format-when-ember-data-does-serializatio
// https://github.com/toranb/ember-data-django-rest-adapter/issues/26
// DS.RESTAdapter.registerTransform("isodate", {
//   deserialize: function(serialized) {
//     return serialized;
//   },

//   serialize: function(deserialized) {
//     return deserialized;
//   }
// });


//Configure the embedded object. Embed UserAddress object in user settings.
// (see: http://stackoverflow.com/questions/14521182/ember-data-does-not-support-embedded-objects/14521612#14521612)
App.Adapter.map('App.UserSettings', {
   address: {
       embedded: 'always'
   }
});

App.UserSettings = DS.Model.extend({
    url: 'users/settings',

    email: DS.attr('string'),
    newsletter: DS.attr('boolean'),
    share_time_knowledge: DS.attr('boolean'),
    share_money: DS.attr('boolean'),
    gender: DS.attr('string'),
    birthdate: DS.attr('birthdate'),
    user_type: DS.attr('string'),
    primary_language: DS.attr('string'),
    address: DS.belongsTo('App.UserAddress')
});

App.UserAddress = DS.Model.extend({
    line1: DS.attr('string'),
    line2: DS.attr('string'),
    city: DS.attr('string'),
    state: DS.attr('string'),
    country: DS.belongsTo('App.Country'),
    postal_code: DS.attr('string')
});


App.UserPreview = DS.Model.extend({
    // We use the same  url as for full User as we almost never use this.
    url: 'users/profiles',

    username: DS.attr('string'),

    // TODO: loose these in favour of short/full name
    first_name: DS.attr('string'),
    last_name: DS.attr('string'),

    full_name: DS.attr('string'),
    short_name: DS.attr('string'),

    name: DS.attr('string'),
    avatar: DS.attr('string'),

    getAvatar: function() {
        if (this.get('avatar')) {
            return this.get('avatar')
        }
        return STATIC_URL + 'images/default-avatar.png'
    }.property('avatar')

});


/*
 A data model representing currently authenticated user.

 Interacts with following authenticated user API:

 Logged in user (GET):            /users/current

 TODO: Should be unified to App.User model.
 */
App.CurrentUser = App.UserPreview.extend({
    url: 'users',

    email: DS.attr('string'),
    primary_language: DS.attr('string'),
    name: DS.attr('string'),
    // This is a hack to work around an issue with Ember-Data keeping the id as 'current'.
    // App.UserSettingsModel.find(App.CurrentUser.find('current').get('id_for_ember'));
    id_for_ember: DS.attr('number'),

    getUser: function(){
        return App.User.find(this.get('id_for_ember'));
    }.property('id_for_ember'),
    getUserPreview: function(){
        return App.UserPreview.find(this.get('id_for_ember'));
    }.property('id_for_ember'),
    isAuthenticated: function(){
        return (this.get('username')) ? true : false;
    }.property('username')
});


App.UserActivation = App.CurrentUser.extend({
    url: 'users/activate'
});


/*
 A model for creating users.

 Interacts with following public API:

 User (POST):   /users/

 */
App.UserCreate = DS.Model.extend({
    url: 'users',

    first_name: DS.attr('string'),
    last_name: DS.attr('string'),
    email: DS.attr('string'),
    password: DS.attr('string')
});


App.PasswordReset = DS.Model.extend({
    url: 'users/passwordset',

    new_password1: DS.attr('string'),
    new_password2: DS.attr('string')
});


App.TimeAvailable = DS.Model.extend({
    url: 'users/time_available',
	type: DS.attr('string'),
	description : DS.attr('string')
});
