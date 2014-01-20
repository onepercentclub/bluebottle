
App.MyProjectOrganisationController = Em.ObjectController.extend(App.Editable, {

    nextStep: 'myProject.legal',

    hasMultipleOrganizations: function(){
        return (this.get('organizations.length') > 1);
    }.property('organizations'),

    shouldSave: function(){
        // Determine if any part is dirty, project or organization.
        if (this.get('isDirty')) {
            return true;
        }
        if (this.get('organization.isDirty')) {
            return true;
        }
        return false;
    }.property('isDirty', 'organization.isDirty'),

    actions: {
        updateRecordOnServer: function(){
            var controller = this;
            var model = this.get('model');
            var organization = model.get('organization');
            var transaction =  this.get('transaction');

            organization.one('didUpdate', function(){
                // Updated organization info.
                controller.transitionToRoute(controller.get('nextStep'));
                $("html, body").animate({ scrollTop: 0 }, 600);
            });
            organization.one('didCreate', function(){
                // Create organization info.
                controller.transitionToRoute(controller.get('nextStep'));
                $("html, body").animate({ scrollTop: 0 }, 600);
            });
            model.one('didUpdate', function(){
                // Updated organization info.
                controller.transitionToRoute(controller.get('nextStep'));
                $("html, body").animate({ scrollTop: 0 }, 600);
            });
            transaction.commit();
        },
        selectOrganization: function(org){
            // Use the same transaction as project
            var model = this.get('model');
            var transaction =  this.get('transaction');
            transaction.add(org);
            this.set('organization', org);
            org.get('projects').pushObject(model);
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


