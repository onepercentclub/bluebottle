App.PaymentController = Em.ObjectController.extend({
    preFixedProfileId: function() {
        return 'tab' + this.get('profile');
    }.property('profile'),

    preFixedProfileContentId: function() {
        return 'tab-content' + this.get('profile');
    }.property('profile'),

    willOpen: function () {
        var _this = this,
            controller = this.get('controller'),
            payment = this.get('model');

        // TODO: we need to send the amount associated with the payment as this
        //       will determine the payment methods. Also, in the future we will
        //       need to send the country with the amount.
        App.PaymentMethod.find().then(
            // Success
            function(methods) {
                _this.set('methods', methods);
            },
            // Failure
            function(methods) {
                throw new Em.error('Fetching PaymentMethod\'s failed!');
            }
        );
    },

    _processPaymentMetadata: function () {
        // integration_url (at PSP)
        // integration_method (GET/POST/PUT)
        // integration_payload (optional metadata required by PSP)
        // integration_type (redirect/popup)
        var meta = this.get('model.integrationDetails');

        if (meta.type == 'redirect') {
            if (meta.method == 'get') {
              var getUrl = this._buildUrl(meta.url, meta.payload);

              window.location.replace(getUrl);
            }
        }
    },

    _buildUrl: function (url, parameters){
        var qs = '';

        for(var key in parameters) {
            var value = parameters[key];
            qs += encodeURIComponent(key) + '=' + encodeURIComponent(value) + '&';
        }
        
        if (qs.length > 0) {
            qs = qs.substring(0, qs.length-1);
            url = url + '?' + qs;
        }

        return url;
    },

    actions: {
        nextStep: function () {
            var _this = this,
                payment = this.get('model');
            payment.save().then(
                // Success
                function (payment) {
                    // Reload the order to receive any backend updates to the order status
                    // NOTE: when using the mock api we will need to manually set the order
                    //       status here.
                    payment.get('order').then(function (order) {
                        order.reload();
                    });

                    // Proceed to the next step based on the status of the payment
                    // 1) Payment status is 'success'
                    // 2) Payment status is 'in_progress'
                    if (payment.get('success')) {
                        // Load the success modal
                        _this.send('modalSlide', 'paymentSuccess', payment);
                    } else {
                        _this._processPaymentMetadata();
                    }
                },
                // Failure
                function (payment) {

                }
            );
        },

        selectedPaymentMethod: function(paymentMethod) {
            this.set('currentPaymentMethod', paymentMethod);
        }
    }

});

// TODO: Adding controllers here for payment success/pending so that the modal 
//       will work with the bb_modal code.
App.PaymentPendingController = Em.Controller.extend();

// Payment success controller extends the TextWallPostNewController as the main
// functionality of the controller is to allow the user to post the the 
// project/fundraiser wall.
App.PaymentSuccessController = App.TextWallPostNewController.extend(BB.ModalControllerMixin, {
    needs: ['projectIndex', 'fundRaiserIndex'],

    _wallPostSuccess: function (record) {
        var _this = this,
            list = _this.get('wallPostList');
        
        list.unshiftObject(record);
        this.send('close');
    },

    // Override the default createNewWallPost to do nothing. We will create
    // the wallpost with the observer above.
    createNewWallPost: Em.K,

    targetType: function () {
      var parentType = this.get('parent_type');
      if (!parentType) return null;

      return parentType.match(/project/) ? 'project' : 'fundraiser';
    }.property('parent_type'),

    wallPostList: function() {
        var parentType = this.get('parent_type');
        if (!parentType) return null;

        var indexType = parentType.match(/project/) ? 'controllers.projectIndex.model' : 'controllers.fundRaiserIndex.model';
        return this.get(indexType);
    }.property('parent_type')
});
