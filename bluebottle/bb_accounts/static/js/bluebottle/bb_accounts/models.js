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
    available_time: DS.attr('string'),
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
        if (this.get('full_name')) {
            return this.get('full_name')
        }
        return this.get('username')
    }.property('first_name', 'full_name'),

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

    email: DS.attr('string'),

    // TODO: loose these in favour of short/full name
    first_name: DS.attr('string'),
    last_name: DS.attr('string'),

    full_name: DS.attr('string'),
    short_name: DS.attr('string'),

    name: DS.attr('string'),
    avatar: DS.attr('string'),

    getFullName: function() {
        if (this.get('full_name')) {
            return this.get('full_name')
        }
        return this.get('username')
    }.property('username', 'full_name'),

    getAvatar: function() {
        if (this.get('avatar')) {
            return this.get('avatar')
        }
        return STATIC_URL + 'images/default-avatar.png'
    }.property('avatar'),

    validEmail: Em.computed.match('email', /.+\@.+\..+/i )

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
    last_login: DS.attr('date'),
    date_joined: DS.attr('date'),

    validEmail: Em.computed.match('email', /.+\@.+\..+/i ),

    donationCount: Em.computed.gt('donation_count', 0),

    projectCount: Em.computed.gt('project_count', 0),

    taskCount: Em.computed.gt('task_count', 0),

    //hasCurrentFundraiser: Em.computed.gt('current_fundraiser.length', 0),

    firstLogin: function () {
        //There is a small lag (ms) between creating the user and getting your token.
        // Therefore we cannot do a direct compare. We allow a 5000ms (5 sec) delay.
        return this.get('last_login') -  this.get('date_joined') < 5000;
    }.property('last_login', 'date_joined'),

    getUser: function(){
        return App.User.find(this.get('id_for_ember'));
    }.property('id_for_ember'),

    getUserPreview: function(){
        return App.UserPreview.find(this.get('id_for_ember'));
    }.property('id_for_ember'),

    isAuthenticated: function(){
        return (this.get('isLoaded') && this.get('username'));
    }.property('username', 'isLoaded')
});

/*
 A model for creating users.

 Interacts with following public API:

 User (POST):   /users/

 */

App.UserCreate = DS.Model.extend(App.ModelValidationMixin, {
    url: 'users',

    first_name: DS.attr('string'),
    last_name: DS.attr('string'),
    email: DS.attr('string'),
    password: DS.attr('string'),
    jwt_token: DS.attr('string', {readOnly: true}),
    emailConfirmation: DS.attr('string'),

    validPassword: function () {
        return this.get('password.length') >= Em.get(App, 'settings.minPasswordLength');
    }.property('password.length'),

    validFirstName: function() {
        return this.get('first_name.length')
    }.property('first_name.length'),

    validLastName: function() {
        return this.get('last_name.length')
    }.property('last_name.length'),

    validEmail: Em.computed.match('email', /.+\@.+\..+/i ),

    matchingEmail: function () {

        if (Em.isEmpty(this.get('email')) || Em.isEmpty(this.get('emailConfirmation'))){
            return false;
        }
        return !Em.compare(this.get('email'), this.get('emailConfirmation'));
    }.property('email', 'emailConfirmation'),

    save: function () {
        this.one('becameInvalid', function(record) {
            // Ember-data currently has no clear way of dealing with the state
            // loaded.created.invalid on server side validation, so we transition
            // to the uncommitted state to allow resubmission
            if (record.get('isNew')) {
                record.transitionTo('loaded.created.uncommitted');
            } else {
                record.transitionTo('loaded.updated.uncommitted');
            }
        });

        return this._super();
    }

});


App.PasswordReset = Em.Object.extend({
    id: null,
    new_password1: null,
    new_password2: null,

    validPassword: function () {
        return this.get('new_password1.length') >= Em.get(App, 'settings.minPasswordLength');
    }.property('new_password1.length'),

    matchingPassword: function() {
        if (Em.isEmpty(this.get('new_password1')) || Em.isEmpty(this.get('new_password2'))){
            return false;
        }
        return !Em.compare(this.get('new_password1'), this.get('new_password2'));
    }.property('new_password1', 'new_password2')
});


App.UserLogin = Em.Object.extend({
    matchId: null,
    matchType: null,
    email: null,
    password: null,
    validEmail: Em.computed.match('email', /.+\@.+\..+/i )
});
