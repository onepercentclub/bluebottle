/*
  Small mixin for handling a successful donation - controllers using this mixin
  should also include the SaveDonationMixin.
*/
App.DonationSuccessMixin = Em.Mixin.create({
});


App.OrderController = Em.ObjectController.extend();

App.OrderSignupController = App.SignupController.extend(App.SaveDonationMixin, App.DonationSuccessMixin, {
    _handleSignupSuccess: function () {
        // Update the user on the order to the current user
        var _this = this,
            donation = this.get('controllers.donation.model'),
            order = donation.get('order');

        order.set('user', App.UserPreview.find(this.get('currentUser.id_for_ember')));
        order.save().then(function (order) {
            // Save the current donation after successful signup
            _this._saveDonation();
        });
    },

    actions: {
        guestPayment: function () {
            this._saveDonation();
        }
    }
});
App.OrderLoginController = App.LoginController.extend(App.SaveDonationMixin, App.DonationSuccessMixin, {
    init: function () {
        this._super();
    },

    _handleLoginSuccess: function () {
        // Update the user on the order to the current user
        var _this = this,
            donation = this.get('controllers.donation.model'),
            order = donation.get('order');

        order.set('user', App.UserPreview.find(this.get('currentUser.id_for_ember')));
        order.save().then(function (order) {
            // Save the current donation after successful login
            _this._saveDonation();
        });
    }
});