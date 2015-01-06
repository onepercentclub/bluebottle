App.BbBackdropComponent = Ember.Component.extend({
    backdropStyle: function() {
        return "background: url(" + this.get('bgImage') + ") no-repeat center top;";
    }.property('bgImage'),
});


App.BbMenuComponent = Ember.Component.extend();


App.BbProfileMenuComponent = App.BbMenuComponent.extend({
    sameUser: function() {
        var user = this.get('user');
        var current_user = App.CurrentUser.find('current'); 
        return user.get('username') == current_user.get('username');
    }.property('user.username'),

    menuItems: function() {
        if (!this.get('sameUser')) return [];

        return [
            Em.Object.create({
                link: "userProfile", 
                label: gettext("Edit profile"),
                icon: "settings-1"
            })
        ];
    }.property('user.username')
});
