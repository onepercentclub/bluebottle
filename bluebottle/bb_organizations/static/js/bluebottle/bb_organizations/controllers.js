App.MyProjectOrganisationController = App.StandardTabController.extend({
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

    isStatusPlanNew: function () {
        return this.get('controllers.myProject.model.isStatusPlanNew');
    }.property('controllers.myProject.model.isStatusPlanNew'),

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

        // No organization selected
        if (!selected) return;

        // Only set the model if the selected org is not new
        if (!selected.get('isNew'))
            this.set('model', selected);
    }.observes('selectedOrganization'),

    actions: {
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
        },

        setFirstSelectableOrganization: function () {
            this.set('selectedOrganization', this.get('firstSelectableOrganization'));
        },

        newOrganization: function () {
            // Only create a new org if the current one isn't new
            if (!this.get('model.isNew'))
              this.set('model', App.MyOrganization.createRecord());
        },

        removeFile: function(doc) {
            var transaction = this.get('model').transaction;
            transaction.add(doc);
            doc.deleteRecord();
            transaction.commit();
        }
    },

    saveData: function(){
        var controller = this;

        return new Ember.RSVP.Promise(function(resolve, reject) {
            $("body").animate({ scrollTop: 0 }, 600);

            var organization = controller.get('model'),
                project = controller.get('controllers.myProject.model'),
                timer;
                
            if (!organization.get('isDirty')) {
                resolve(gettext('Model is not dirty.'));
                return;
            }

            if (organization.get('isNew')) {
                organization.one('didCreate', function(){
                    Ember.run.next(function() {
                        // Now that the org is saved we can save the documents too.
                        controller.get('tempDocuments').forEach(function(doc){
                            doc.save();
                            organization.get('documents').addObject(doc);
                        });

                        clearTimeout(timer);
                        resolve(gettext('Model saved successfully.'));
                    });

                });
            } else {
                organization.one('didUpdate', function() {
                    clearTimeout(timer);
                    resolve(gettext('Model saved successfully.'));
                });
            }

            organization.set('errors', {});
            organization.save();

            // TODO: ugly hack until we start using Ember Data 1.0+ with it's
            //       save/find... thenable niceties
            timer = setTimeout( function () {
                // should never get here - didCreate, becameInvalid etc events should be triggered.
                reject(gettext('Hey! What are you doing here? Saving model failed.'));
            }, 10 * 1000);
        });
    }
});

App.MyProjectBankController = App.StandardTabController.extend({
    needs: ['myProject'],

	init: function () {
		this._super();
		if (this.get('model.validEuropeanBankOrganization')){
			this.set('inEurope', true);
		} else {
            if (this.get('model.account_number')){
                this.set('inEurope', false);
            } else {
    			this.set('inEurope', true);
            }
		}
	},
    previousStep: "myProject.organisation",
    nextStep: 'myProject.submit',

    isStatusPlanNew: function () {
        return this.get('controllers.myProject.model.isStatusPlanNew');
    }.property('controllers.myProject.model.isStatusPlanNew'),

	setInEurope: function () {
		if (this.get('model.validEuropeanBankOrganization')){
			this.set('inEurope', true);
		} else {
            if (this.get('model.account_number')){
                this.set('inEurope', false);
            } else {
    			this.set('inEurope', true);
            }
        }
	}.observes('model.validBankAccountInfo'),

    actions: {
      showInEurope: function(event) {
          this.set('inEurope', true);
      },

      showOutEurope: function() {
          this.set('inEurope', false);
      }
    },
    outsideEurope: Em.computed.not('inEurope')
});


