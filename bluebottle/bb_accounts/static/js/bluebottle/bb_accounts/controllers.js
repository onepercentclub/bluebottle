/*
 * Controllers
 */

App.SignupController = Ember.ObjectController.extend({
    needs: "currentUser",
    createAttempt: false,

    validationErrors: function () {
        // Only check error validations after submitting
        if (!this.get('createAttempt'))
            return;

        var errors = Em.Object.create(this.get('model.errors'))

        if (!this.get('model.matchingEmail')) {
            var msg = gettext('Emails don\'t match');
            if (errors.get('email'))
                errors.get('email').push(msg);
            else
                errors.set('email', [msg]);
        }
        if (!this.get('model.validPassword')) {
            var msg = gettext('Password is too short (at least 5 characters)');
            if (errors.get('password'))
                errors.get('password').push(msg);
            else
                errors.set('password', [msg]);
        }

        return errors
    }.property('model.errors', 'model.matchingEmail', 'model.validPassword'),


    actions: {
        createUser: function(user) {
            var _this = this;

            this.set('createAttempt', true);
            user.save().then(function(createdUser) {
                var response = {
                    token: createdUser.get('jwt_token')
                };

                return App.AuthJwt.processSuccessResponse(response).then(function (currentUser) {
                    // This is for successfully setting the currentUser.
                    _this.set('controllers.currentUser.model', App.CurrentUser.find('current'));
                    // TODO: close the modal when we start using one for signup
                    //      _this.send('closeAllModals');
                    // For now we just transition to home page
                    _this.transitionToRoute('/');
                }, function () {
                    // Handle failure to create currentUser
                });
            }, function() {
                // Handle error message here!
            });
        }
    }
});


// Inspiration from:
// http://stackoverflow.com/questions/14388249/accessing-controllers-from-other-controllers
App.CurrentUserController = Ember.ObjectController.extend({
    init: function() {
        debugger
        this._super();
        this.set("model", App.CurrentUser.find('current'));
    }
});


App.UserController = Ember.Controller.extend({
    needs: "currentUser"
});


App.UserProfileController = Ember.ObjectController.extend(App.Editable, {

	availableTimes: function() {
		return App.TimeAvailable.find();
	}.property(),

    updateCurrentUser: function(record) {
        var currentUser = App.CurrentUser.find('current');
        currentUser.reload();
    }

});


App.UserSettingsController = Em.ObjectController.extend(App.Editable, {
    needs: ['userProfile'],
    userTypeList: (function() {
        var list = Em.A();
        list.addObject({ name: gettext('Person'), value: 'person'});
        list.addObject({ name: gettext('Company'), value: 'company'});
        list.addObject({ name: gettext('Foundation'), value: 'foundation'});
        list.addObject({ name: gettext('School'), value: 'school'});
        list.addObject({ name: gettext('Club / Association'), value: 'group'});
        return list;
    }).property(),

});


App.UserOrdersController = Em.ObjectController.extend(App.Editable, {

    // Don't prompt the user to save if the 'fakeRecord' is set.
    stopEditing: function() {
        var record = this.get('model');
        if (!record.get('fakeRecord')) {
            this._super()
        }
    },

    recurringPaymentActive: '',

    // Initialize recurringPaymentActive
    initRecurringPaymentActive: function() {
        if (this.get('isLoaded')) {
            if (this.get('active')) {
                this.set('recurringPaymentActive', 'on')
            } else {
                this.set('recurringPaymentActive', 'off')
            }
        }
    }.observes('isLoaded'),

    updateActive: function() {
        if (this.get('recurringPaymentActive') != '') {
            this.set('active', (this.get('recurringPaymentActive') == 'on'));
        }
    }.observes('recurringPaymentActive')
});


App.UserModalController = Ember.ObjectController.extend({
	// actions: function() {
	// 	goToProfile: function() {
	// 		
	// 	}
	// },
    loadProfile: function() {
        var model = this.get('model');
        var id = model.get('id');

        if (id == "current") {
            // Get user id for current user
            id = model.get('id_for_ember');
        }

        this.set('model', App.User.find(id));
    }.observes('model')
});

App.LoginController = Em.Controller.extend({
    needs: ['currentUser'],

    loginTitle: 'Log in to <Bluebottle Project>',
    username: null,
    password: null,

    actions: {
        login: function () {
            Ember.assert("LoginController needs implementation of authorizeUser.", this.authorizeUser !== undefined);

            var _this = this;
            return this.authorizeUser(this.get('username'), this.get('password')).then(function (user) {
                _this.set('controllers.currentUser.model', user);
                _this.send('closeAllModals');
            }, function (error) {
                _this.set('error', error);
            });
        },
        requestPasswordReset: function() {
            // Close previous modal, if any.
            $('.close').click();

            var modalPaneTemplate = '<div>{{view templateName="request_password_reset"}}</div>';

            Bootstrap.ModalPane.popup({
                classNames: ['modal'],
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),

                callback: function(opts, e) {
                    if (opts.secondary) {
                        var $btn        = $(e.target),
                            $modal      = $btn.closest('.modal'),
                            $emailInput = $modal.find('#passwordResetEmail'),
                            $error      = $modal.find('#passwordResetError'),
                            email       = $emailInput.val();

                        $.ajax({
                            type: 'PUT',
                            url: '/api/users/passwordreset',
                            data: JSON.stringify({email: email}),
                            dataType: 'json',
                            contentType: 'application/json; charset=utf-8',
                            success: function() {
                                var message = gettext("YOU'VE GOT MAIL!<br /><br />We've sent you a link to reset your password, so check your mailbox.<br /><br />(No mail? It might have ended up in your spam folder)");
                                var $success = $("<p>" + message +"</p>");

                                $modal.find('.modal-body').html($success);
                                $btn.remove();
                            },
                            error: function(xhr) {
                                var error = $.parseJSON(xhr.responseText);
                                $error.html(error.email);
                                $error.removeClass('hidden');
                                $error.fadeIn();
                                $emailInput.addClass('error').val();
                                $emailInput.keyUp(function() {
                                    $error.fadeOut();
                                });
                            }
                        });

                        return false;
                    }
                }
            })
        }
    }
});

App.PasswordResetController = Ember.ObjectController.extend({
    needs: ['login'],

    resetDisabled: (function() {
        return !(this.get('new_password1') || this.get('new_password2'));
    }).property('new_password1', 'new_password2'),

    resetPassword: function(record) {
        var passwordResetController = this;

        record.one('didUpdate', function() {
            var loginController = passwordResetController.get('controllers.login');
            var view = App.LoginView.create({
                next: "/"
            });
            view.set('controller', loginController);

            loginController.set('post_password_reset', true);

            var modalPaneTemplate = '{{view view.bodyViewClass}}';

            Bootstrap.ModalPane.popup({
                classNames: ['modal'],
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
                bodyViewClass: view
            });
        });

        record.save();
    }
});


App.ProfileController = Ember.ObjectController.extend({
    addPhoto: function(file) {
        this.set('model.file', file);
    }
});

