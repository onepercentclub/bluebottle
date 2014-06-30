/*
 * Controllers
 */

App.SignupController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {
    createAttempt: false,
    errorDefinitions : [
        {'property': 'email', 'validateProperty': 'matchingEmail', 'message': gettext('Emails doesn\'t match')},
        {'property': 'password', 'validateProperty': 'validPassword', 'message': gettext('Password needs to be at least 5 charcaters long')}
    ],

    init: function() {
        this._super();

        var user = App.UserCreate.createRecord({
            first_name: '',
            last_name: '',
        });

        this.set('model', user);
    },
    actions: {
        createUser: function(user) {
            var _this = this;
            // Ignoring API errors here, we are passing ignoreApiErrors=true
            _this.set('validationErrors', _this.validateErrors(_this.errorDefinitions, _this.get('model.'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                return false
            }
            user.save().then(function(newUser) {
                var response = {
                    token: newUser.get('jwt_token')
                };

                return App.AuthJwt.processSuccessResponse(response).then(function (currentUser) {
                    // This is for successfully setting the currentUser.
                    _this.set('currentUser.model', App.CurrentUser.find('current'));
                    _this.send('close');
                    
                    // For now we just transition to home page
                    _this.transitionToRoute('/');
                }, function () {
                    // Handle failure to create currentUser
                    _this.set('validationErrors', _this.validateErrors(_this.errorDefinitions, _this.get('model')));
                });

            }, function (failedUser) {
                // If the user create failed due to a conflict then transition to the 
                // login modal so the user can sign in.
                if (failedUser.errors.conflict) {
                    var loginObject = Em.Object.create({username: failedUser.get('email')});

                    _this.send('modalFlip', 'login', loginObject);
                } else {
                    // Handle error message here!
                    _this.set('validationErrors', _this.validateErrors(_this.errorDefinitions, _this.get('model')));
                }
            });
        }
    }
});


App.UserController = Ember.Controller.extend({});


// This is only being used as a means for other controllers to access the currentUser
// This is done by injection in the currentUser intializer.
// TODO: we should just set the currentUser property on the application controller or route
//       and inject that so that it is available from all controllers.
App.CurrentUserController = Ember.ObjectController.extend({});


App.UserProfileController = Ember.ObjectController.extend(App.Editable, {
    availableTimes: function() {
        return App.TimeAvailable.find();
    }.property(),
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

App.LoginController = Em.ObjectController.extend(BB.ModalControllerMixin, {
    content: null,
    loginTitle: gettext('Log in to <Bluebottle Project>'),

    actions: {
        login: function () {
            Ember.assert("LoginController needs implementation of authorizeUser.", this.authorizeUser !== undefined);

            var _this = this;
            return this.authorizeUser(this.get('username'), this.get('password')).then(function (user) {
                _this.set('currentUser.model', user);
                _this.send('closeModal');
                _this.send('setFlash', 'Testing!')
            }, function (error) {
                _this.set('error', error);
            });
        },


    }
});

App.PasswordRequestController = Ember.Controller.extend(BB.ModalControllerMixin, {
    needs: ['login'],
    requestResetPasswordTitle : gettext('Password reset request'),
    contents: null,

    actions: {
        requestReset: function() {
            var _this = this;
            return Ember.RSVP.Promise(function (resolve, reject) {
                var email = _this.get('controllers.login.username'),
                    hash = {
                        url: '/api/users/passwordreset',
                        dataType: "json",
                        type: 'put',
                        data: JSON.stringify({email: email}),
                        contentType: 'application/json; charset=utf-8'
                    };

                hash.success = function (response) {
                    _this.send('modalFlip', 'passwordRequestSuccess');
                };

                hash.error = function (response) {
                    var error = $.parseJSON(response.responseText);
                    _this.set('error', error);
                };

                Ember.$.ajax(hash);
            });
        }
    }
});

App.PasswordRequestSuccessController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
    needs: ['login'],
    successRequestPasswordTitle : gettext("Help is on its way"),
    successMessage: gettext("We have sent a password reset link to")
});

App.PasswordResetController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
    needs: ['login'],
    resetPasswordTitle : gettext('Reset your password'),


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

