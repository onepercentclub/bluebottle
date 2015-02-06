App.SuggestionController = Em.ObjectController.extend({

    createOrganization: function() {
        var model = this.get('model');

        var organization = App.MyOrganization.createRecord({
            name: model.get('org_name'),
            current_name: model.get('org_contactname'),
            phone_number: model.get('org_phone'),
            website: model.get('org_website)'),
            email: model.get('org_email')
        });
        
        return organization;
    },

    updateSuggestion: function(project) {
        var model = this.get('model');

        model.set('status', 'in_progress');
        model.set('project', project);

        return model;
    },

    createProject: function(myOrganization) {
        var model = this.get('model');

        var project = App.MyProject.createRecord({
            title: model.get('title'),
            pitch: model.get('pitch'),
            theme: model.get('theme'),
            //organization: myOrganization
        });

        return project;

    },

    actions: {

        adoptSuggestion: function() {
            var _this = this;
            debugger
            _this.createOrganization().save().then(function(organization) {

                _this.createProject(organization).save().then(function(project) {

                    _this.updateSuggestion(project).save().then(function() {

                        _this.send('closeModal');
                        // Redirect to project edit flow
                        _this.transitionTo('myProject.pitch', project)                  
                    });      
                }, function(err) {
                    debugger
                });
            });            



        }
    }
});

App.SuggestionListController = Em.ArrayController.extend({
    totalSuggestions: function() {
        return this.get('model.length');
    }.property("@each"),

    hasSuggestions: function() {
        return this.get('totalSuggestions') > 0;
    }.property('totalSuggestions'),

    actions: {
        showSuggestion: function(suggestion) {
            this.send('openInExtraLargeBox', "suggestion", suggestion);
        }
    }
});

