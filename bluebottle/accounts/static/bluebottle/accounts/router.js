App.Router.map(function() {

	this.resource('signup');

    this.resource('user', {path: '/member'}, function() {
        this.resource('userProfile', {path: '/profile/'});
        this.resource('userSettings', {path: '/settings'});
        
        // TODO: isolate this
        this.resource('userOrders', {path: '/orders'});
    });

    this.route('userActivate', {path: '/activate/:activation_key'});
    this.resource('passwordReset', {path: '/passwordreset/:reset_token'});
});