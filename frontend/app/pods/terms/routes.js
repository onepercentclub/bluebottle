App.ApplicationRoute.reopen({
    checkTerms: function() {
        var _this = this,
            controller = this.get('controller');

        controller.set('terms', App.Terms.find('current'));
        var agreement = App.TermsAgreement.find('current').then(function(agreement){
            _this.controllerFor('currentUser').set('agreedToTerms', agreement);
        });
    }.on('setupCompleted')
});