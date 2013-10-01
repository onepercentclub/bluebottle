/*
*  Views
*/

App.UserModalView = Em.View.extend({
    templateName: 'user_modal'
});


App.LoginView = Em.View.extend({
    templateName: 'login',
	didInsertElement: function() {
		$("#login-form").validate({
            messages: {
                username: {
                    email: gettext("Please use your email address to log in.")
                }
            },
            onfocusout: true
        });
	},
    next: function() {
        return  String(window.location);
    }.property()
});
