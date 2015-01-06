/**
 * Router mapping
 */
App.Router.map(function(){
    this.resource('signup');

    this.resource('user', {path: '/member'}, function() {
        this.resource('userProfile', {path: '/profile/'});
        this.resource('userSettings', {path: '/settings'});

        // TODO: isolate this
        this.resource('userOrders', {path: '/orders'});
    });
    this.resource('viewProfile', {path: '/member/profile/:user_id'});

    this.resource('passwordReset', {path: '/passwordreset/:reset_token'});

    this.resource('disableAccount', {path: '/disable/:user_id/:token'});

    this.resource('passwordRequest', {path: '/passwordrequest/:email'});
});

/*
 *  Routes
 */


App.UserIndexRoute = Em.Route.extend({
    beforeModel: function() {
        this.transitionTo('userProfile');
    }
});


App.UserProfileRoute = Em.Route.extend(App.ScrollToTop, App.AuthenticatedRouteMixin, App.TrackRouteActivateMixin, {
    trackEventName: "View profile",
    model: function() {
        var route = this;
        return App.CurrentUser.find('current').then(function(user) {
            return App.User.find(user.get('id_for_ember'));
        });
    },

    deactivate: function() {
        this.controllerFor('userProfile').stopEditing();
    }
});

App.ViewProfileRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        var model = App.User.find(params.user_id);
        var route = this;
        model.on('becameError', function() {
            route.transitionTo('error.notFound');
        });
        return model;
    }
});

App.UserSettingsRoute = Em.Route.extend(App.ScrollToTop, App.AuthenticatedRouteMixin, App.TrackRouteActivateMixin, {
    trackEventName: "View settings",
    model: function() {
        var route = this;

        return App.CurrentUser.find('current').then(function(user) {
            return App.UserSettings.find(user.get('id_for_ember'));
        });
    },

    deactivate: function() {
        this.controllerFor('userSettings').stopEditing();
    }
});

App.PasswordRequestRoute = Em.Route.extend({
    renderTemplate: function() {
        this.render('home');
        this.send('openInBox', 'passwordRequest');
    },

    model: function(params) {
        return Em.Object.create({email: params.email, failedToken: true})
    }
});

App.PasswordResetRoute = Em.Route.extend({
    renderTemplate: function() {
        this.render('home');
        this.send('openInBox', 'passwordReset');
    },

    model: function(params) {
        return App.PasswordReset.create({
            id: params.reset_token
        });
    },

    beforeModel: function(transition) {
        return Ember.RSVP.Promise(function (resolve, reject) {
            var hash = {
                url: '/api/users/passwordset/' + transition.params.reset_token,
                type: 'get',
                contentType: 'application/json; charset=utf-8'
            };
            
            hash.success = function(response) {
                Ember.run(null, resolve, null)
            };

            hash.error = function(response) {
                Ember.run(null, reject, JSON.parse(response.responseText));
            };

            Ember.$.ajax(hash);
        })
    },
    actions: {
        error: function(error, transition) {
            transition.abort()
            this.transitionTo('passwordRequest', error.email)
        }
    }
});

App.DisableAccountRoute = Em.Route.extend({
    init: function(){
        this._super();
    },

   renderTemplate: function() {
       this.render('home');
       this.send('openInBox', 'disableAccount');
   },

    model: function(params){
        return Em.Object.create({user_id: params.user_id, token: params.token});
    }
});
