App.SuggestionController = Em.ObjectController.extend({

    createOrganization: function() {
        var model = this.get('model');

        return new Ember.RSVP.Promise(function(resolve, reject){

                        App.MyOrganization.createRecord({
                            name: model.get('org_name'),
                            current_name: model.get('org_contactname'),
                            phone_number: model.get('org_phone'),
                            website: model.get('org_website)'),
                            email: model.get('org_email')

                        }).save().then(function (organization) {
                                resolve(organization);
                            }, function (newDonation) {
                                reject(organization.errors);
                            });
                    });
    },

    updateSuggestion: function(project) {
        
        var model = this.get('model');

        model.set('status', 'in_progress');
        model.set('project', project);

        model.save();

        return model;
    },

    createProject: function(myOrganization) {
        var model = this.get('model');

        return new Ember.RSVP.Promise(function(resolve, reject){

                        App.MyProject.createRecord({
                                    title: model.get('title'),
                                    pitch: model.get('pitch'),
                                    theme: model.get('theme'),
                                    deadline: model.get('deadline'),
                                    //destination: model.get('destination'),
                                    organization: myOrganization

                        }).save().then(function (project) {
                                resolve(project);
                            }, function (project) {
                                reject(project.errors);
                            });
                    });

    },

    actions: {

        adoptSuggestion: function() {
            var _this = this;
            
            _this.createOrganization().then(function(organization) {

                _this.createProject().then(function(project) {

                    _this.updateSuggestion(project);
                    _this.send('closeModal');

                    // Redirect to project edit flow
                    _this.transitionTo('myProject.pitch', project);

                    //});      
                }, function(err) {
                    console.log(err);
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

