
/* Controllers */

App.ContactMessageController = Em.ObjectController.extend({
    updateRecordOnServer: function(){
        var controller = this;
        var model = this.get('model');
        model.one('becameInvalid', function(record){
            model.set('errors', record.get('errors'));
        });
        model.save();
    }
});

