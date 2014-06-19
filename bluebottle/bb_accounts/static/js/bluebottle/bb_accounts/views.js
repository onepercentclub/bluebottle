/*
*  Views
*/

App.UserModalView = Em.View.extend({
    templateName: 'user_modal'
});

App.LoginView = Em.View.extend({
    templateName: 'login',

    next: function() {
        return  String(window.location);
    }.property()
});

App.ItemSelectView = Em.Select.extend({
    optionValuePath: "content.id",
    optionLabelPath: "content.name",
    prompt: "Pick an item"
});

