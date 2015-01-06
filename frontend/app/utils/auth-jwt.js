/*
 Include the JWT token in the header of all api requests.
 */

jwtTokenJustRenewed = false;

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (sameOrigin(settings.url) && App.get('jwtToken')) {
            // Send the token to same-origin, relative URLs only. 
            // Fetching JWT Token occurs during login.
            xhr.setRequestHeader("Authorization", "JWT " + App.get('jwtToken'));
        }
    },
    complete: function(xhr, settings) {
        // Check if the response has a refreshed jwt token
        var refreshToken = xhr.getResponseHeader('Refresh-Token');

        // Value will be formatted as: 'JWT eyJhbGciOiJIUzI1NiIsInR5cCI6I...'
        if (!jwtTokenJustRenewed && refreshToken && (match = refreshToken.match(/JWT\s(.*)/))) {
                Em.Logger.debug('Successfully refreshed JWT token.');
                var newToken = match[1];

                localStorage['jwtToken'] = newToken;
                App.set('jwtToken', newToken);
                
                // Set a timer so that responses which returned within the next 1sec also containing 
                // a renewed token won't cause multiple changes to the localStorage['jwtToken'] and 
                // the App jwtToken property.
                jwtTokenJustRenewed = true;
                Ember.run.later(this, function() {
                    jwtTokenJustRenewed = false;
                }, 1000);

        } else if (xhr.status == 401) {
            Em.Logger.debug('Failed JWT authorization. Logging user out.');

            // If the request returns with a 401 - Unauthorized then we logout the user.
            // TODO: this needs some UX work to handle this situation in a more userfriendly way.
            App.__container__.lookup('route:application').send('logout', '/');
        }
    }
});

App.AuthJwt = {
    // Use this function to process the response containing a JWT token
    // It should be used with a promise and the response of the form:
    //    {token: '123abc'}
    processSuccessResponse: function (response) {
        return Ember.RSVP.Promise(function (resolve, reject) {
            // User authentication succeeded. Store the token:
            // 1) in the local store for use if the user reloads the page
            // 2) in a property on the App 
            localStorage['jwtToken'] = response.token;
            App.set('jwtToken', response.token);

            // In Ember Data < beta the App.CurrentUser gets stuck in the root.error
            // state so we need to force a transition here before trying to fetch the
            // user again.
            var currentUser = App.CurrentUser.find('current');
            if (currentUser.get('currentState.error.stateName') == 'root.error') {
                currentUser.transitionTo('deleted.saved');
                return App.CurrentUser.find('current').then( function (user) {
                    Ember.run(null, resolve, user);
                }, function (user) {
                    if (response.error != undefined) {
                        Ember.run(null, reject, response.error);
                    } else {
                        Ember.run(null, reject, gettext('Failed to create currentUser'));
                    }
                });
            } else {
                Ember.run(null, resolve, currentUser);
            }
        });
    }
}

/*
 Ensure we reload the JWT token from the local store if possible.
 This needs to happen before the ember store loads so the api 
 requests can include the JWT token if available.
 */
// TODO: Enable this once we work out why we can't use the jwt token after
//       a reload. It seems it is only valid for one session??
Ember.Application.initializer({
     name: 'setJwtToken',
     before: 'currentUser',
     initialize: function(container, application) {
         var jwtToken = localStorage['jwtToken'];
         if (jwtToken)
             App.set('jwtToken', jwtToken);
     }
});

/* 
 A mixin for JWT authentication - this will be called from the BB LoginController
 when the user submits the login (email/password) form. 
 */
App.AuthJwtMixin = Em.Mixin.create({
    authorizeUser: function (email, password) {
        var _this = this,
            email = _this.get('email'),
            password = _this.get('password');
        
        // Clear any existing tokens which might be present but expired
        _this.send('clearJwtToken');

        return Ember.RSVP.Promise(function (resolve, reject) {
            var hash = {
              url: "/api/token-auth/",
              dataType: "json",
              type: 'post',
              data: {
                  email: email,
                  password: password
              }
            };
           
            hash.success = function (response) {
                return App.AuthJwt.processSuccessResponse(response).then(function (user) {
                    Ember.run(null, resolve, user);
                }, function (error) {
                    Ember.run(null, reject, error);
                });
            };
           
            hash.error = function (response) {
                var error;
                if (!Em.isEmpty(response.responseText))
                    error = JSON.parse(response.responseText);

                Ember.run(null, reject, error);
            };
           
            Ember.$.ajax(hash);
        });
    }
});

/*
 Custom logout action for JWT
 */
App.LogoutJwtMixin = Em.Mixin.create({
    refreshToken: function () {
        return Ember.RSVP.Promise(function (resolve, reject) {
            if (localStorage.jwtToken) {
                // Check if user has authentication token and if they do then request 
                // a token refresh from the server
                hash = {
                    url: '/api/token-auth-refresh/',
                    type: 'post',
                    dataType: "json",
                    contentType: 'application/json; charset=utf-8',
                    data: {
                      'token': localStorage.jwtToken
                    }
                }

                hash.success = function (response) {
                    Em.Logger.debug('Successfully refreshed JWT token.');

                    localStorage['jwtToken'] = response.token;
                    App.set('jwtToken', response.token);

                    Ember.run(null, resolve, response.token);
                };

                hash.failure = function (response) {
                    Em.Logger.debug('Failed to refresh JWT token.');

                    var error = JSON.parse(response.responseText);

                    Ember.run(null, reject, error);
                };

                Ember.$.ajax(hash);
            }
        });
    },
    actions: {
        clearJwtToken: function () {
            App.set('jwtToken', null);
            delete localStorage['jwtToken'];
        },
        logout: function (redirect) {
            var _this = this,
                applicationController = this.controllerFor('application');

            if (typeof redirect === 'undefined')
                redirect = true;

            Ember.run.next(function() {
                // Clear the jwtToken references
                _this.send('clearJwtToken');

                function handleCurrentUser() {
                    // Redirect to?? If the user is in a restricted route then 
                    // they should be redirected to the home route. For now we 
                    // always force them to the home
                    if (redirect)
                        _this.transitionTo('home');
                }

                // Clear the current user details
                applicationController.set('currentUser.model', null);
                App.CurrentUser.find('current').then(function (currentUser) {
                    currentUser.store.unloadRecord(currentUser);
                    handleCurrentUser();
                }, function () {
                    handleCurrentUser();
                });
            });
        }
    }
});

/*
 Login With route to login using JWT

 To add a next link (for deep linking) add a url encoded path after '?'
 Eg: /login-with/<token>?%2fprojects will redirect to #!/projects after setting the jwt token.



 */

App.Router.map(function() {
    this.resource('loginWith', {path: '/login-with/:token'});
    this.resource('logout', {path: '/logout'});

});

App.ApplicationRoute.reopen(App.LogoutJwtMixin);

App.LoginWithRoute = Em.Route.extend({
    beforeModel: function(transition) {
        var _this = this,
            params = transition.params.token.split('?'),
            token = {token: params[0]},
            next = params[1];

        transition.abort();
        App.AuthJwt.processSuccessResponse(token).then(function (user) {
            _this.set('currentUser.model', user);
            if (next) {
                _this.transitionTo(decodeURIComponent(next));

            } else {
                _this.transitionTo('/');
            }
        });
    }
});

App.LogoutRoute = Em.Route.extend({
    beforeModel: function(transition) {
        transition.abort();
        App.__container__.lookup('route:application').send('logout', '/');
        this.transitionTo('/');
    }
});