App.ContactMessage = DS.Model.extend({
    url: 'pages/contact',

    name: DS.attr('string'),
    email: DS.attr('string'),
    message: DS.attr('string'),

    isComplete: function(){
        if (this.get('name') && this.get('email') && this.get('message')){
            return true;
        }
        return false;
    }.property('name', 'email', 'message'),

    isSent: function(){
        if (this.get('id')){
            return true;
        }
        return false;
    }.property('id')
});