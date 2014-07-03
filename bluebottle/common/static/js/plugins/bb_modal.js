BB = {};

BB.ModalControllerMixin = Em.Mixin.create({
    // This can be overridden with code to respond with when the 
    // modal content is about to be replace with new content.
    // This will usually involve clearing the model data => form fields
    willClose: Em.K,

    actions: {
        close: function () {
            this.send('closeModal');
        }
    }
})

BB.ModalMixin = Em.Mixin.create({
    actions: {
        willTransition: function(newController) {
            // Handle any cleanup for the previously set content for the modal
            var modalContainer = this.controllerFor('modalContainer'),
                previousController = modalContainer.get('currentController');

            if (previousController && Em.typeOf(previousController.willClose) == 'function')
                previousController.willClose();

            // Set the currentController property on the container to this new controller
            // so we can call willClose on it later
            if (newController)
                modalContainer.set('currentController', newController);
        },

        openInFullScreenBox: function(name, context) {
            this.send('openInBox', name, context, 'full-screen');
        },

        openInScalableBox: function(name, context) {
            this.send('openInBox', name, context, 'scalable');
        },

        openInBigBox: function(name, context) {
            this.send('openInBox', name, context, 'large');
        },

        openInBox: function(name, context, type, callback) {
            // Setup the modal container
            var modalContainer = this.controllerFor('modalContainer');
            this.render('modalContainer', {
                into: 'application',
                outlet: 'modalContainer',
                controller: modalContainer
            });

            this.send('scrollDisableEnable');
            this.send('closeKeyModal', '27');

            // Setup the modal content and set the model if passed
            var controller = this.controllerFor(name);
            if (Em.typeOf(context) != 'undefined')
                controller.set('model', context);

            // Handle any cleanup for the previously set content for the modal
            this.send('willTransition', controller);

            return this.render(name, {
                into: 'modalContainer',
                outlet: 'modalFront',
                controller: controller
            });
        },
        
        closeModal: function() {
            var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
                _this = this;

            // Handle any cleanup for the previously set content for the modal
            this.send('willTransition');

            $('.modal-fullscreen-background').one(animationEnd, function(){
                // Finally clear the outlet
                _this.disconnectOutlet({
                    outlet: 'modalContainer',
                    parentView: 'application'
                });
            });

            this.send('scrollDisableEnable');

            $('.modal-fullscreen-background').addClass('is-inactive');
        },

        scrollDisableEnable: function() {
            $('body').toggleClass('is-stopped-scrolling');
        },

        closeKeyModal: function(key) {
            var self = this;
            $(document).on('keydown', function(e) {
                if(e.keyCode == key) {
                    self.send('closeModal');
                }
            });
        },

        closeClickModal: function() {
            var string = event.target.className.substring();
            var className = string.indexOf("is-active");

            if (className > 0) {
                this.send('closeModal');
            }
        },

        modalFlip: function(name, context) {
            var controller = this.controllerFor(name);

            if (Em.typeOf(context) != 'undefined')
                controller.set('model', context);

            // Handle any cleanup for the previously set content for the modal
            this.send('willTransition', controller);

            this.render(name, {
                into: 'modalContainer',
                outlet: 'modalBack',
                controller: controller
            });

            $('#card').addClass('flipped');
            $('#card').attr('class', 'flipped');
            $('.front').attr('class', 'front');
            $('.back').attr('class', 'back');
        },

        modalFlipBack: function(name) {
            var controller = this.controllerFor(name);
            
            // Handle any cleanup for the previously set content for the modal
            this.send('willTransition', controller);

            this.render(name, {
                into: 'modalContainer',
                outlet: 'modalFront',
                controller: controller
            });

            $('#card').removeClass('flipped');
        },

        modalSlideLeft: function(name) {
            var controller = this.controllerFor(name);
            
            // Handle any cleanup for the previously set content for the modal
            this.send('willTransition', controller);

            this.render(name, {
                into: 'modalContainer',
                outlet: 'modalBack',
                controller: controller
            });
            $('.front').removeClass('slide-in-left');
            $('.back').removeClass('slide-out-right');
            $('.front').addClass('slide-out-left');
            $('.back').addClass('slide-in-right');
        },

        modalSlideRight: function(name) {
            var controller = this.controllerFor(name);
            
            // Handle any cleanup for the previously set content for the modal
            this.send('willTransition', controller);

            this.render(name, {
                into: 'modalContainer',
                outlet: 'modalFront',
                controller: controller
            });
            $('.front').removeClass('slide-out-left');
            $('.back').removeClass('slide-in-right');
            $('.front').addClass('slide-in-left');
            $('.back').addClass('slide-out-right');
        }
    },
});

BB.ModalContainerController = Em.ObjectController.extend(BB.ModalControllerMixin, {
    currentController: null
});

BB.ModalContainerView = Em.View.extend({
    tagName: null,
    template: Ember.Handlebars.compile([
        '<div class="modal-fullscreen-background is-active" {{action "closeClickModal"}}>',
            '<div class="modal-fullscreen-container">',
                '<div id="card">',
                    '<figure class="front">',
                        '<div class="modal-fullscreen-item">{{outlet "modalFront"}}</div>',
                    '</figure>',
                    '<figure class="back">',
                        '<div class="modal-fullscreen-item">{{outlet "modalBack"}}</div>',
                    '</figure>',
                '</div>',
            '</div>',
        '</div>'].join("\n"))
});