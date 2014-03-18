/*
 Mixin that controllers with editable models can use. E.g. App.UserProfileController

 @see App.UserProfileRoute and App.UserProfileController to see it in action.
 */
App.SaveOnExitMixin = Ember.Mixin.create({

    actions : {
        goToStep: function(step){
            $("body").animate({ scrollTop: 0 }, 600);
            var model = this.get('model');
            var controller = this;

            if (!model.get('isDirty')) {
                if (step) controller.transitionToRoute(step);
            }

            model.one('becameInvalid', function(record) {
                // Ember-data currently has no clear way of dealing with the state
                // loaded.created.invalid on server side validation, so we transition
                // to the uncommitted state to allow resubmission
                if (record.get('isNew')) {
                    record.transitionTo('loaded.created.uncommitted');
                } else {
                    record.transitionTo('loaded.updated.uncommitted');
                }
            });

            if (model.get('isNew')) {
                model.one('didCreate', function(){
                    if (step) controller.transitionToRoute(step);

                });
            } else {
                model.one('didUpdate', function(){
                    if (step) controller.transitionToRoute(step);
                });
            }
            
            model.set('errors', {});
            model.save();
        },

        goToPreviousStep: function(){
            var step = this.get('previousStep');
            this.send('goToStep', step);
        },

        goToNextStep: function(){
            var step = this.get('nextStep');
            this.send('goToStep', step);
        },

        goToNextNoSave: function(){
            if (this.get('nextStep')){
                this.transitionToRoute(this.get('nextStep'));
            }
        },

        goToPreviousNoSave: function(){
            if (this.get('previousStep')){
                this.transitionToRoute(this.get('previousStep'));
            }
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

    }
});

App.SimpleControllerObjectStatus = Em.Mixin.create({

    status: function () {
        if (!this.get('model.isSaving') && !this.get('model.isDirty')) {
            return 'ready';
        } else if (this.get('model.isSaving')) {
            return 'busy';
        } else if (this.get('model.isDirty')) {
            return 'dirty';
        }
    }.property('model.isSaving', 'model.isDirty'),
    
});

App.StandardTabController = Em.ObjectController.extend(App.SimpleControllerObjectStatus, App.SaveOnExitMixin, {});