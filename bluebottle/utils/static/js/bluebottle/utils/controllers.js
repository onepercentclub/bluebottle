App.ShareEmbeddedController = Em.ObjectController.extend({
    needs: ['project'],

    getModel: function() {
        this.set('model', App.ProjectPreview.find(this.get('controllers.project.id')));
    }.observes('controllers.project.id'),

    embedCode: function(){
        var code = '<script type="text/javascript" data-language="en" src="https://onepercentclub.com/static/assets/js/widget.js" data-id="opcwidget" data-project="' 
                    + this.controllerFor('project').get('model.id') + '"></script>'
        return code;
    }.property()

});
