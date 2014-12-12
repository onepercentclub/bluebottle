App.TermsModalController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
    needs: ['currentUser'],

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