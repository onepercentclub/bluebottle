/*
*  Views
*/

App.SignupView = App.FormView.extend({
    submitAction: 'signup'
});

App.UserModalView = App.FormView.extend({
    templateName: 'user_modal'
});

App.LoginView = App.FormView.extend({
    submitAction: 'login',

    next: function() {
        return  String(window.location);
    }.property()
});

App.PasswordResetView = App.FormView.extend({
    submitAction: 'resetPassword'
});

App.PasswordRequestView = App.FormView.extend({
    submitAction: 'requestReset'
});


App.ItemSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: gettext("Pick an item")
});

App.DisableAccountView = App.FormView.extend({
     templateName: 'disable'
});

