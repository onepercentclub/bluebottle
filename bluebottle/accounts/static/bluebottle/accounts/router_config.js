/*
* accounts_router is called in the main router to add the routes
* NOTE: this MUST come before the Router Mapping. More recent Ember versions
* allow App.Router.map() to be called multiple times, but RC6 doesn't.
*/

var accounts_router = function(){
	this.resource('signup');

    this.resource('user', {path: '/member'}, function() {
        this.resource('userProfile', {path: '/profile/'});
        this.resource('userSettings', {path: '/settings'});
        
        // TODO: isolate this
        this.resource('userOrders', {path: '/orders'});
    });

    this.route('userActivate', {path: '/activate/:activation_key'});
    this.resource('passwordReset', {path: '/passwordreset/:reset_token'});
};