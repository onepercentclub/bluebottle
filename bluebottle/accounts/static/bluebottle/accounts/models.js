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
    first_name: DS.attr('string'),
    last_name: DS.attr('string'),
    about: DS.attr('string'),
    why: DS.attr('string'),
    availability: DS.attr('string'),
    location: DS.attr('string'),

    picture: DS.attr('image'),

    website: DS.attr('string'),
    date_joined: DS.attr('date'),
    file: DS.attr('string'),

    // post-only fields (i.e. only used for user creation)
    email: DS.attr('string'),
    password: DS.attr('string'),

    getPicture: function() {
        if (this.get('picture')) {
            return MEDIA_URL + this.get('picture.large')
        }
        return STATIC_URL + 'images/default-avatar.png'
    }.property('picture'),

    getAvatar: function(){
        if (this.get('picture')) {
            return this.get('picture.square')
        }
        return STATIC_URL + 'images/default-avatar.png'
    }.property('picture'),

    full_name: function() {
        if (!this.get('first_name') && !this.get('last_name')) {
            return this.get('username');
        }
        return this.get('first_name') + ' ' + this.get('last_name');
    }.property('first_name', 'last_name'),

    user_since: function() {
        return Globalize.format(this.get('date_joined'), 'd');
    }.property('date_joined')

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

App.UserSettings = DS.Model.extend({
    url: 'users/settings',

    email: DS.attr('string'),
    newsletter: DS.attr('boolean'),
    share_time_knowledge: DS.attr('boolean'),
    share_money: DS.attr('boolean'),
    gender: DS.attr('string'),
    birthdate: DS.attr('string'),
    user_type: DS.attr('string'),
    primary_language: DS.attr('string'),

    // Address
    line1: DS.attr('string'),
    line2: DS.attr('string'),
    city: DS.attr('string'),
    state: DS.attr('string'),
    country: DS.attr('string'),
    postal_code: DS.attr('string')
});


App.UserPreview = DS.Model.extend({
    // There is no url for UserPreview because it's embedded.
    url: undefined,

    username: DS.attr('string'),
    first_name: DS.attr('string'),
    last_name: DS.attr('string'),
    avatar: DS.attr('string'),

    full_name: function() {
        if (!this.get('first_name') && !this.get('last_name')) {
            return this.get('username');
        }
        return this.get('first_name') + ' ' + this.get('last_name');
    }.property('first_name', 'last_name'),

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
    getUser: function(){
        return App.User.find(this.get('id_for_ember'));
    }.property('id_for_ember'),
    primary_language: DS.attr('string'),

    isAuthenticated: function(){
        return (this.get('username')) ? true : false;
    }.property('username'),

    // This is a hack to work around an issue with Ember-Data keeping the id as 'current'.
    // App.UserSettingsModel.find(App.CurrentUser.find('current').get('id_for_ember'));
    id_for_ember: DS.attr('number')
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