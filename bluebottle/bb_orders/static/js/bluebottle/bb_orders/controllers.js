App.OrderController = Em.ObjectController.extend();

/*
 Mixin to be used by the login and signup controllers to handle
 assigning the current user to the current order.
 */
App.OrderAssignUserMixin = Em.Mixin.create({
    _assignUser: function () {
        // Update the user on the order to the current user
        var _this = this,
            donation = this.get('controllers.donation.model'),
            order = donation.get('order');
        App.UserPreview.find(this.get('currentUser.id_for_ember')).then(function (user) {
            order.set('user', user).send('becomeDirty');
            order.save().then(function (savedOrder) {
                // Save the current donation after successful signup
                _this._saveDonation().then(function () {
                    // Reload the order to fetch the embedded donations
                    savedOrder.reload();
                });
            });
        });
    }
})

App.OrderSignupController = App.SignupController.extend(App.OrderAssignUserMixin, App.SaveDonationMixin, {
    _handleSignupSuccess: function () {
        this._assignUser();
    },

    _handleSignupConflict: function (failedUser) {
        var conflict = failedUser.errors.conflict,
            loginObject = App.UserLogin.create({
                matchId: conflict.id,
                matchType: conflict.type,
                email: failedUser.get('email')
            });

        this.send('modalContent', 'orderLogin', loginObject);
    },

    actions: {
        guestPayment: function () {
            this._saveDonation();
        }
    }
});

App.OrderLoginController = App.LoginController.extend(App.OrderAssignUserMixin, App.SaveDonationMixin, {
    _handleLoginSuccess: function () {
        this._assignUser();
    }
});
