/*
 * Controllers
 */

App.SignupController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {
    createAttempt: false,
    fieldsToWatch: ['password.length', 'email', 'emailConfirmation'],
    requiredFields: ['password.length', 'email', 'emailConfirmation', 'first_name', 'last_name'],

    init: function() {
        this._super();

        this.set('errorDefinitions', [
            {
                'property': 'first_name',
                'validateProperty': 'validFirstName',
                'message': gettext('First Name can\'t be left empty'),
                'priority': 3
            },
            {
                'property': 'last_name',
                'validateProperty': 'validLastName',
                'message': gettext('Surname can\'t be left empty'),
                'priority': 4
            },
            {
                'property': 'email',
                'validateProperty': 'matchingEmail',
                'message': gettext('Emails don\'t match'),
                'priority': 1
            },
            {
                'property': 'password',
                'validateProperty': 'validPassword',
                'message': Em.get(App, 'settings.minPasswordError'),
                'priority': 2
            }
        ]);

        this._clearModel();
    },

    _clearModel: function () {
        var user = App.UserCreate.createRecord({
            first_name: '',
            last_name: '',
        });

        this.set('model', user);
    },

    // pass the to the fieldStrength function the field we want to evaluate
    passwordStrength: function(){
        return this.fieldStrength(this.get('password'))
    }.property('password.length'),

    willClose: function () {
        this._clearModel();

        // Clear the notifications
        this.set('errorsFixed', false);
        this.set('validationErrors', null);
        this.set('isBusy', false);
    },

    didError: function () {
        if (this.get('error')) {
            // Error set so not busy anymore
            this.set('isBusy', false);

            // Call error action on the modal
            this.send('modalError');
        }
    }.observes('error'),

    actions: {
        signup: function() {
            var _this = this,
                user = this.get('model');

            // Enable the validation of errors on fields only after pressing the signup button
            _this.enableValidation()

            // Clear the errors fixed message
            _this.set('errorsFixed', false);

            // Ignoring API errors here, we are passing ignoreApiErrors=true
            _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                this.send('modalError');
                return false
            }

            // Set is loading property until success or error response
            _this.set('isBusy', true);

            user.save().then(function(newUser) {
                var response = {
                    token: newUser.get('jwt_token')
                };

                return App.AuthJwt.processSuccessResponse(response).then(function (authorizedUser) {
                    // This is for successfully setting the currentUser.
                    _this.set('currentUser.model', authorizedUser);

                    // This is the users first login so flash a welcome message
                    _this.send('setFlash', _this.get('currentUser.welcomeMessage'));

                    // Call the loadNextTransition in case the user was unauthenticated and was
                    // shown the sign in / up modal then they should transition to the requests route
                    _this.send('loadNextTransition', '/');

                    // Close the modal
                    _this.send('close');
                }, function () {
                    _this.set('isBusy', false);

                    // Handle failure to create currentUser
                    _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model')));
                });

            }, function (failedUser) {
                _this.set('isBusy', false);

                // If the user create failed due to a conflict then transition to the 
                // login modal so the user can sign in.
                // We set matchType = social / email so the login controller can notify the user.
                if (failedUser.errors.conflict) {
                    var conflict = failedUser.errors.conflict,
                        loginObject = Em.Object.create({
                            matchId: conflict.id,
                            matchType: conflict.type,
                            email: failedUser.get('email')
                        });

                    _this.send('modalFlip', 'login', loginObject);
                } else {
                    _this.send('modalError');
                    // Handle error message here!
                    _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model')));
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
App.CurrentUserController = Ember.ObjectController.extend(BB.ModalControllerMixin,{
    welcomeMessage: function() {
        var msg1 = gettext('Welcome ') + this.get('first_name') + '.',
            msg2 = gettext(' Ready to do some good?'),
            msg = msg1 + ' ' + msg2;
        return msg
    }.property()
});


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


App.UserModalController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
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

App.LoginController = Em.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {
    loginTitle: gettext('Log in to <Bluebottle Project>'),
    fieldsToWatch: ['email.length', 'password.length'],
    requiredFields: ['email', 'password'],

    init: function () {
        this._super();

        this.set('errorDefinitions', [
            {
                'property': 'email',
                'validateProperty': 'email.length',
                'message': gettext('Email required'),
                'priority': 1
            },
            {
                'property': 'password',
                'validateProperty': 'password.length',
                'message': gettext('Password required'),
                'priority': 2
            }
        ]);

        this._clearModel();
    },

    _clearModel: function () {
        this.set('content', Em.Object.create());
    },

    willClose: function () {
        this.set('password', null);
        this.set('matchType', null);
        this.set('matchId', null);
        this.set('error', null);
        this.set('isBusy', false);
    },

    socialMatch: Em.computed.equal('model.matchType', 'social'),
    emailMatch: Em.computed.equal('model.matchType', 'email'),
    userMatch: Em.computed.or('socialMatch', 'emailMatch'),

    matchedUser: function () {
        if (this.get('matchId'))
            return App.UserPreview.find(this.get('matchId'));
        else
            return null;
    }.property('userMatch'),

    // TODO: Refactor the error handlers into an ember mixin.
    //       Setting/clearing errors should be done in the same
    //       way for all forms.
    didError: function (error) {
        if (this.get('error')) {
            // Error set so not busy anymore
            this.set('isBusy', false);

            // Call error action on the modal
            this.send('modalError');
        }
    }.observes('error'),

    actions: {
        login: function () {
            Ember.assert("LoginController needs implementation of authorizeUser.", this.authorizeUser !== undefined);
            var _this = this;

            // Enable the validation of errors on fields only after pressing the signup button
            _this.enableValidation()

            // Ignoring API errors here, we are passing ignoreApiErrors=true
            _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                this.send('modalError');
                return false
            }

            // Set is loading property until success or error response
            this.set('isBusy', true);

            return _this.authorizeUser(_this.get('email'), _this.get('password')).then(function (user) {
                _this.set('currentUser.model', user);

                // Call the loadNextTransition in case the user was unauthenticated and was
                // shown the sign in / up modal then they should transition to the requests route
                _this.send('loadNextTransition');
                // Close the modal
                _this.send('close');
            }, function (error) {
                _this.set('error', error);
            });
        },

        signup: function () {
            this.send('modalFlip', 'signup');
        },

        passwordRequest: function () {
            var email = Em.Object.create({email: this.get('email')})
            this.send('modalSlide', 'passwordRequest', email);
        }
    }
});

App.PasswordRequestController = Ember.ObjectController.extend(App.ControllerValidationMixin, BB.ModalControllerMixin, {
    requestResetPasswordTitle : gettext('Trouble signing in?'),
    fieldsToWatch: ['email.length'],
    requiredFields: ['email.length'],
    content: null,

    init: function () {
        this._super();

        this.set('errorDefinitions', [
            {
                'property': 'email',
                'validateProperty': 'email.length',
                'message': gettext('Email required'),
                'priority': 1
            }
        ]);

        this._clearContent();
    },

    _clearContent: function () {
        this.set('content', Em.Object.create({}));
    },

    willClose: function () {
        this.set('isBusy', false);
    },

    didError: function () {
        if (this.get('error')) {
            // Error set so not busy anymore
            this.set('isBusy', false);

            // Call error action on the modal
            this.send('modalError');
        }
    }.observes('error'),

    actions: {
        requestReset: function() {
            var _this = this;

            // Early out if the input is empty
            if (Em.isEmpty(this.get('email'))) {
                this.send('modalError');
                return
            }

            this.set('isBusy', true);
            this.set('error', null);

            return Ember.RSVP.Promise(function (resolve, reject) {
                var hash = {
                        url: '/api/users/passwordreset',
                        dataType: "json",
                        type: 'put',
                        data: JSON.stringify(_this.get('content')),
                        contentType: 'application/json; charset=utf-8'
                    };

                hash.success = function (response) {
                    _this.send('close');
                    _this.send('setFlash', gettext("We\'ve sent a password reset link to your inbox"));
                    Ember.run(null, resolve, response);
                };

                hash.error = function (response) {
                    var msg = gettext('There is no account associated with the email.')
                    _this.set('error', msg);

                    Ember.run(null, reject, msg);
                };

                Ember.$.ajax(hash);
            });
        }
    }
});


App.PasswordResetController = Ember.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {
    needs: ['login'],
    resetPasswordTitle : gettext('Make it one to remember'),
    successMessage: gettext('We\'ve updated your password, you\'re all set!'),
    fieldsToWatch: ['new_password1.length, new_password2.length'],
    requiredFields: ['new_password1','new_password2'],

    init: function() {
        this._super();

        this.set('errorDefinitions', [
            {
                'property': 'new_password1',
                'validateProperty': 'validPassword',
                'message': Em.get(App, 'settings.minPasswordError'),
                'priority': 1
            },
            {
                'property': 'new_password2',
                'validateProperty': 'matchingPassword',
                'message': gettext('Passwords don\'t match'),
                'priority': 2
            }
        ]);
    },

    matchingPassword: function () {
        return !Em.compare(this.get('new_password1'), this.get('new_password2'));
    }.property('new_password1.length', 'new_password2.length'),

    _clearModel: function () {
        this.set('content', Em.Object.create());
    },

    willClose: function () {
        this._clearModel();

        // Clear the notifications
        this.set('validationErrors', null);
        this.set('error', null);
    },

    didError: function () {
        if (this.get('error')) {
            // Error set so not busy anymore
            this.set('isBusy', false);

            // Call error action on the modal
            this.send('modalError');
        }
    }.observes('error'),

    // pass the to the fieldStrength function the field we want to evaluate
    passwordStrength: function(){
        return this.fieldStrength(this.get('new_password1'))
    }.property('new_password1.length'),

    actions: {
        resetPassword: function (record) {
            var _this = this,
                model = this.get('model');

            // Enable the validation of errors on fields only after pressing the reset button
            _this.enableValidation()

            // Ignoring API errors here, we are passing ignoreApiErrors=true
            _this.set('validationErrors', _this.validateErrors(_this.errorDefinitions, _this.get('model'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                return false
            }

            this.set('isBusy', true);
            this.set('error', null);

            return Ember.RSVP.Promise(function (resolve, reject) {
                var token = _this.get('model.id'),
                    hash = {
                        url: '/api/users/passwordset/' + token,
                        dataType: "json",
                        type: 'put',
                        data: JSON.stringify({
                            new_password1: model.get('new_password1'),
                            new_password2: model.get('new_password2')
                        }),
                        contentType: 'application/json; charset=utf-8'
                    };

                hash.success = function (response) {
                    if (!response.token)
                        Ember.run(null, reject, 'JWT token not returned!');

                    App.AuthJwt.processSuccessResponse(response).then(function (user) {
                        // Set the current user and close the modal
                        _this.set('currentUser.model', user);
                        _this.send('setFlash', _this.get('successMessage'));
                        _this.send('close');

                        // Resolve the promise
                        Ember.run(null, resolve, user);
                    }, function (error) {
                        // Handle failure to create currentUser
                        _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model')));

                        // Reject the promise
                        Ember.run(null, reject, error);
                    });
                };

                hash.error = function (response) {
                    var msg = gettext('Invalid token, try request a new password again')
                    _this.set('error', msg);

                    // Reject the promise
                    Ember.run(null, reject, msg);
                };

                Ember.$.ajax(hash);
            });
        }
    }
});

App.ProfileController = Ember.ObjectController.extend({
    addPhoto: function(file) {
        this.set('model.file', file);
    }
});


App.DisableAccountController = Ember.ObjectController.extend(BB.ModalControllerMixin, {
    disableAccountTitle: gettext('If you leave me now...'),
    successMessage: gettext('The account was disabled'),

    init: function() {
        this._super();
    },

    userPreview: function(){
        return App.User.find(this.get('model.user_id'));
    }.property('model.user_id'),

    actions: {
        disableAccount: function(record){
            var _this = this,
                model = this.get('model');

            return Ember.RSVP.Promise(function (resolve, reject) {
                var user_id = _this.get('model.user_id'),
                    token = _this.get('model.token'),
                    hash = {
                        url: '/api/users/disable-account/' + user_id + '/' + token + '/',
                        type: 'post'
                    };

                hash.success = function (response) {
                    _this.send('setFlash', _this.get('successMessage'));
                    _this.send('close');

                    Ember.run(null, resolve, gettext("Success"));
                    _this.transitionToRoute('/');
                };

                hash.error = function (response) {
                    var msg = gettext('Error, invalid token');
                    _this.set('error', msg);

                    // Reject the promise
                    Ember.run(null, reject, msg);
                };

                Ember.$.ajax(hash);
            });
        },

        cancelDisable: function(){
            this.send('close');
            this.transitionToRoute('/');
        }
    }

});
