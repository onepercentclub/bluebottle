/*
 * Router mapping
 */

App.Router.map(function() {
    this.resource('contactMessage', {path: '/contact'});
});

/* Contact Page */

App.ContactMessageRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        var store = this.get('store');
        model = App.ContactMessage.createRecord();

        // get the name and email from the currently logged in user
        App.CurrentUser.find('current').then(function(user) {
        	model.set('name', user.get('full_name'));
        	model.set('email', user.get('email'));
        });
        return model;
    }
});
