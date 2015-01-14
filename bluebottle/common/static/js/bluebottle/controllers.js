////
// Standard Tab Controller with: 
//   Save model on exit
//   Status property associated model
//   Model save actions
//
App.StandardTabController = Em.ObjectController.extend(App.ControllerObjectSaveMixin, App.ControllerObjectStatusMixin, App.SaveOnExitMixin, {});

// Extend BB Modal
App.ModalContainerController = BB.ModalContainerController.extend();

App.ShareFlyer = Em.Object.extend(App.Serializable, {
    share_name: null,
    share_email: null,
    share_motivation:  null,
    share_cc: false
});

App.ShareFlyerController =  Em.ObjectController.extend(BB.ModalControllerMixin, App.ControllerValidationMixin, {
    init: function () {
        this._super();

        this.set('errorDefinitions', [
            {
                'property': 'share_name',
                'validateProperty': 'share_name.length',
                'message': gettext('Please provide the recipient\'s name'),
                'priority': 1
            },
            {
                'property': 'share_email',
                'validateProperty': {
                    'test': emailValidator
                },
                'message': gettext('Please provide the recipient\'s email'),
                'priority': 2
            },
            {
                'property': 'share_motivation',
                'validateProperty': 'share_motivation.length',
                'message': gettext('Please provide a motivation'),
                'priority': 3
            }
        ]);

    },

    actions: {
        submit: function() {
            var _this = this,
                model = this.get('model');

            _this.enableValidation();
            _this.set('errorsFixed', false);

            _this.set('validationErrors', _this.validateErrors(_this.get('errorDefinitions'), _this.get('model'), true));

            // Check client side errors
            if (_this.get('validationErrors')) {
                this.send('modalError');
                return false;
            }

            this.set('error', null);

            _this.send("closeModal");
            model.submit("/utils/share_flyer").then(
                function(res) {
                    // what is a valid flash type?
                    _this.send("setFlash", gettext("Great! Your project flyer will be shared."), "success", 2000);
                },
                function(res) {
                    // what is a valid flash type?
                    _this.send("setFlash", res, "success", 2000);
                }
            );
        }
    }
});

