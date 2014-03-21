
App.MyProjectOrganisationController = Em.ObjectController.extend(App.ControllerObjectSaveMixin, App.ControllerObjectStatusMixin, {
    needs: ['myProject'],

    tempDocuments: Em.A(),
    organizations: Em.A(),

    previousStep: 'myProject.story',
    nextStep: 'myProject.submit',

    hasMultipleOrganizations: function () {
      return this.get('organizations.length') > 1;
    }.property('organizations.length'),

    // Triggered when the user selects one of the existing organisations for this user.
    setOrganization: function () {
        if (this.get('selectedOrganization')) {
            if (this.get('isNew')) {
                // Set the current organization name to something that
                // makes sense in the picklist
                console.log(this.get('model'));
                console.log(this.get('name'));
                this.set('name', '- New Organisation -');
                console.log(this.get('model'));
                console.log(this.get('name'));
            }
            this.set('model', this.get('selectedOrganization'));
            this.connectOrganizationToProject();
        }
    }.observes('selectedOrganization'),

    connectOrganizationToProject: function(){
        var project = this.get('controllers.myProject.model');
        var organization = this.get('model');

        // Set organization on project.
        project.set('organization', organization);
        if (project.get('isNew')) {
            project.transitionTo('loaded.created.uncommitted');
        } else {
            project.transitionTo('loaded.updated.uncommitted');
        }
        // If no project title: Use organization name for that.
        if (!project.get('title')) {
            project.set('title', organization.get('name'));
        }
        project.save();
    },

    isPhasePlanNew: function () {
      return this.get('controllers.myProject.model.isPhasePlanNew');
    }.property('controllers.myProject.model.isPhasePlanNew'),

    actions: {
        goToStep: function(step){
            $("body").animate({ scrollTop: 0 }, 600);

            var controller = this;
            var organization = this.get('model');
            var project = this.get('controllers.myProject.model');

            if (!organization.get('isDirty')) {
                if (step) controller.transitionToRoute(step);
            }

            organization.one('becameInvalid', function(record) {
                // Ember-data currently has no clear way of dealing with the state
                // loaded.created.invalid on server side validation, so we transition
                // to the uncommitted state to allow resubmission
                if (record.get('isNew')) {
                    record.transitionTo('loaded.created.uncommitted');
                } else {
                    record.transitionTo('loaded.updated.uncommitted');
                }
            });

            if  (organization.get('isNew')) {
                organization.one('didCreate', function(){
                    Ember.run.next(function() {
                        // Now that the org is saved we can save the documents too.
                        controller.get('tempDocuments').forEach(function(doc){
                            doc.save();
                            organization.get('documents').addObject(doc);
                        });
                        controller.connectOrganizationToProject();
                        if (step) controller.transitionToRoute(step);
                    });

                });
            } else {
                organization.one('didUpdate', function(){
                    if (step) controller.transitionToRoute(step);
                });
            }

            organization.set('errors', {});
            organization.save();
        },


        goToPreviousStep: function(){
            var step = this.get('previousStep');
            this.send('goToStep', step);
        },

        goToNextStep: function(){
            var step = this.get('nextStep');
            this.send('goToStep', step);
        },
        removeFile: function(doc) {
            var transaction = this.get('model').transaction;
            transaction.add(doc);
            doc.deleteRecord();
            transaction.commit();
        }

    },

    addFile: function(file) {
        var store = this.get('store');
        var doc = store.createRecord(App.MyOrganizationDocument);
        doc.set('file', file);
        var organization = this.get('model');
        // If the organization is already saved we can save the doc right away
        if (organization.get('id')) {
            doc.set('organization', organization);
            doc.save();
        } else {
            this.get('tempDocuments').addObject(doc);
        }
    }
});

App.MyProjectBankController = Em.ObjectController.extend(App.Editable, {

    nextStep: 'myProject.submit',

    shouldSave: function(){
        // Determine if any part is dirty, project plan, org or any of the org addresses
        if (this.get('isDirty')) {
            return true;
        }
        if (this.get('organization.isDirty')) {
            return true;
        }
        return false;
    }.property('organization.isLoaded', 'isDirty'),

    actions: {
        updateRecordOnServer: function(){
            var controller = this;
            var model = this.get('model.organization');
            model.one('becameInvalid', function(record){
                model.set('errors', record.get('errors'));
            });
            model.one('didUpdate', function(){
                controller.transitionToRoute(controller.get('nextStep'));
                window.scrollTo(0);
            });
            model.one('didCreate', function(){
                controller.transitionToRoute(controller.get('nextStep'));
                window.scrollTo(0);
            });

            model.save();
        }
    }
});


