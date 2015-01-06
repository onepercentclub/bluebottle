App.ApplicationController.reopen({
    checkAgreement: function() {
        if (! this.get('terms.isLoaded') || ! this.get('currentUser.agreedToTerms.isLoaded')) return;

        var _this = this,
            terms = this.get('terms'),
            agreement = this.get('currentUser.agreedToTerms');
            
        if (! Em.isEmpty(terms.get('contents')) && terms.get('isLoaded') && terms.get('contents') &&
            agreement && agreement.get('isLoaded') && !agreement.get('created') && !this.get('termsModalOpen')) {
            _this.set('termsModalOpen', true);
            _this.send('openInBigBox', 'terms_modal', terms);
        }
    }.observes('currentUser.agreedToTerms.isLoaded', 'terms.isLoaded'),

    rejectedTerms: function(){
        if (this.get('currentUser.rejectedTerms')) {
            this.send('logout');
        }
    }.observes('currentUser.rejectedTerms')
});


App.TermsModalController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
    needs: ['currentUser'],

    willOpen: function() {
        this.container.lookup('controller:modalContainer').set('type', 'large');
    },

    willClose: function(){
        // Set the terms to rejected when modal is closed.
        var terms = this.get('model'),
            agreement = App.TermsAgreement.createRecord({terms: terms});
        if (terms && agreement && agreement.get('created')){
            return true;
        } else {
            this.send('rejectTerms');
        }
    },


    actions: {
        acceptTerms: function(terms){
            var _this = this;
            if (!terms) {
                terms = this.get('model');
            }
            var agreement = App.TermsAgreement.createRecord({terms: terms});
            agreement.save().then(function(agreement){
                _this.set('controllers.currentUser.agreedToTerms', agreement);
                _this.send('close');

            })
        },
        rejectTerms: function(){
            if (!this.get('controllers.currentUser.agreedToTerms.terms')) {
                this.set('controllers.currentUser.rejectedTerms', true);
            }
        }
    }
});