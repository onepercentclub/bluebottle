App.TermsModalController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
    needs: ['currentUser'],

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
        }
    }


});