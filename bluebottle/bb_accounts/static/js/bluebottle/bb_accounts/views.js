/*
*  Views
*/

App.UserModalView = Em.View.extend({
    templateName: 'user_modal'
});

App.LoginView = Em.View.extend({
    templateName: 'login',

    clearForm: function () {
        var controller = this.get('controller');

        controller.set('username', null);
        controller.set('password', null);
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

