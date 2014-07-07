/*
*  Views
*/

App.SignupView = Em.View.extend({
    keyPress: function (evt) {
        var code = evt.which;
        // If enter key pressed
        if (code == 13) {
            evt.preventDefault();
            this.get('controller').send('signup');
        }
    }
});

App.UserModalView = Em.View.extend({
    templateName: 'user_modal'
});

App.LoginView = Em.View.extend({
    templateName: 'login',
    
    next: function() {
        return  String(window.location);
    }.property(),

    keyPress: function (evt) {
        var code = evt.which;
        // If enter key pressed
        if (code == 13) {
            evt.preventDefault();
            this.get('controller').send('login');
        }
    }
});

App.PasswordResetView = Em.View.extend({
    clearForm: function () {
        var controller = this.get('controller');

        controller.set('new_password1', null);
        controller.set('new_password2', null);
        controller.set('error', null);
    }.on('willInsertElement'),

    next: function() {
        return  String(window.location);
    }.property()

});

App.ItemSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: "Pick an item"
});

App.DisableAccountView = Em.View.extend({
     templateName: 'disable'

});

