
App.MyProjectOrganisationController = Em.ObjectController.extend({
    needs: ['myProject'],

    previousStep: 'myProject.story',
    nextStep: 'myProject.submit',

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
                        organization.get('documents').forEach(function(doc){
                            console.log('saving document...');
                            doc.save();
                        });
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
        },

        save: function() {
            $("body").animate({ scrollTop: 0 }, 600);
            var model = this.get('model');

            model.set('errors', {});
            model.save();
        },

        rollback: function() {
            $("body").animate({ scrollTop: 0 }, 600);
            var organization = this.get('model');
            organization.rollback();
        }

    },

    addFile: function(file) {
        var store = this.get('store');
        var doc = store.createRecord(App.MyOrganizationDocument);
        doc.set('file', file);
        var organization = this.get('model');
        doc.set('organization', organization);
        // If the organization is already saved we can save the doc right away
        if (organization.get('id')) {
            console.log('saving document...');
            doc.save();
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


