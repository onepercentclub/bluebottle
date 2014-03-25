
App.MyProjectOrganisationController = Em.ObjectController.extend(App.ControllerObjectSaveMixin, App.ControllerObjectStatusMixin, {
    needs: ['myProject'],

    tempDocuments: Em.A(),
    organizations: Em.A(),
    
    previousStep: 'myProject.story',
    nextStep: 'myProject.submit',

    // Before the organisation is saved the documents will
    // be temporarily stored in the tempDocuments array.
    attachedDocuments: function () {
        if (this.get('model.isNew'))
            return this.get('tempDocuments');
        else
            return this.get('model.documents');
    }.property('model.documents.length', 'tempDocuments.length'),

    hasMultipleOrganizations: function () {
      return this.get('organizations.length') > 1;
    }.property('organizations.length'),

    isPhasePlanNew: function () {
        return this.get('controllers.myProject.model.isPhasePlanNew');
    }.property('controllers.myProject.model.isPhasePlanNew'),

    actions: {
        newOrganization: function () {
            // Only create a new org if the current one isn't new
            if (!this.get('model.isNew'))
              this.set('model', App.MyOrganization.createRecord());
        },

        goToStep: function(step){
            $("body").animate({ scrollTop: 0 }, 600);

            var controller = this;
            var organization = this.get('model');
            var project = this.get('controllers.myProject.model');

            if (!organization.get('isDirty')) {
                if (step) controller.transitionToRoute(step);
            }

            if  (organization.get('isNew')) {
                organization.one('didCreate', function(){
                    Ember.run.next(function() {
                        // Now that the org is saved we can save the documents too.
                        controller.get('tempDocuments').forEach(function(doc){
                            doc.save();
                            organization.get('documents').addObject(doc);
                        });

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


