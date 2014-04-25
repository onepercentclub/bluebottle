
App.MyProjectOrganisationController = Em.ObjectController.extend(App.ControllerObjectSaveMixin, App.ControllerObjectStatusMixin, {
    needs: ['myProject'],

    tempDocuments: Em.A(),
    organizations: Em.A(),
    selectedOrganization: null,
    
    previousStep: 'myProject.story',
    nextStep: 'myProject.bank',

    // Before the organisation is saved the documents will
    // be temporarily stored in the tempDocuments array.
    attachedDocuments: function () {
        if (this.get('model.isNew'))
            return this.get('tempDocuments');
        else
            return this.get('model.documents');
    }.property('model.documents.length', 'tempDocuments.length'),

    hasSelectableOrganizations: function () {
        return this.get('selectableOrganizations.length') > 0;
    }.property('selectableOrganizations.length'),

    hasOneSelectableOrganization: function () {
        return this.get('selectableOrganizations.length') == 1;
    }.property('selectableOrganizations.length'),

    firstSelectableOrganization: function () {
        if (this.get('hasSelectableOrganizations')) {
            return this.get('selectableOrganizations.0');          
        }

    }.property('hasSelectableOrganizations'),

    isPhasePlanNew: function () {
        return this.get('controllers.myProject.model.isPhasePlanNew');
    }.property('controllers.myProject.model.isPhasePlanNew'),

    canSave: function () {
        var name = this.get('model.name');
        return (name && name.length > 0);
    }.property('model.name'),

    selectableOrganizations: function() {
        return this.get('organizations').filterProperty('isNew', false);
    }.property('organizations.@each.isNew'),

    setOrganization: function () {
        // Only set the actual organization when the selected one is an already saved org
        var selected = this.get('selectedOrganization');

        if (!selected.get('isNew'))
            this.set('model', selected);
    }.observes('selectedOrganization'),

    actions: {
        setFirstSelectableOrganization: function () {
            this.set('selectedOrganization', this.get('firstSelectableOrganization'));
        },

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

App.MyProjectBankController = App.StandardTabController.extend({
    previousStep: "myProject.organisation",
    nextStep: 'myProject.submit',

    actions: {
      showInEurope: function(event) {
          this.set('inEurope', true);
      },

      showOutEurope: function() {
          this.set('inEurope', false);
      }
    },

	setInEurope: function () {
		if (this.get('model.validEuropeanBankOrganization')){
			this.set('inEurope', true);
		} else if (this.get('model.validNotEuropeanBankOrganization')){
			this.set('inEurope', false);
		}
	}.observes('model.validBankAccountInfo'),

	outsideEurope: Em.computed.not('inEurope')

});


