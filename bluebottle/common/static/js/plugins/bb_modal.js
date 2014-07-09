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
        modalWillTransition: function(name, side, context) {
            // Handle any cleanup for the previously set content for the modal
            var modalContainer = this.controllerFor('modalContainer'),
                previousController = modalContainer.get('currentController');

            // Call willClose on the previous modal - if defined
            if (previousController && Em.typeOf(previousController.willClose) == 'function')
                previousController.willClose();

            // Set the currentController property on the container to this new controller
            // so we can call willClose on it later
            if (name) {
                var newController = this.controllerFor(name);
                modalContainer.set('currentController', newController);

                // Setup the modal content and set the model if passed
                if (Em.typeOf(context) != 'undefined')
                    newController.set('model', context);

                this.render(name, {
                    into: 'modalContainer',
                    outlet: side,
                    controller: newController
                });
            }
        },


        openInFullScreenBox: function(name, context) {
            this.send('openInOldBox', name, context, 'full-screen');
        },

        openInScalableBox: function(name, context) {
            this.send('openInOldBox', name, context, 'scalable');
        },

        openInBigBox: function(name, context) {
            this.send('openInOldBox', name, context, 'large');
        },

        
        // Add openInBox as function on ApplicationRoute so that it can be used
        // outside the usual template/action context
        openInOldBox: function(name, context, type, callback) {
            // Close all other modals.
            $('.close-modal').click();

            // Get the controller or create one
            var controller = this.controllerFor(name);
            if (context) {
                controller.set('model', context);
            }

            if (typeof type === 'undefined')
              type = 'normal'

            var classNames = [type];

            // Get the view. This should be defined.
            var view = App[name.classify() + 'View'].create();
            view.set('controller', controller);

            var modalPaneTemplate = ['<div class="modal-wrapper"><a class="close" rel="close">&times;</a>{{view view.bodyViewClass}}</div>'].join("\n");

            var options = {
                classNames: classNames,
                defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
                bodyViewClass: view
            }

            if (callback) {
                options.callback = callback;
            }

            Bootstrap.ModalPane.popup(options);
        },

        openInBox: function(name, context, type, callback) {
            // Setup the modal container
            var modalContainer = this.controllerFor('modalContainer');
            this.render('modalContainer', {
                into: 'application',
                outlet: 'modalContainer',
                controller: modalContainer
            });

            this.send('scrollDisable');
            this.send('closeKeyModal', '27');

            // Handle any cleanup for the previously set content for the modal
            this.send('modalWillTransition', name, 'modalFront', context);
        },

        addRemoveClass: function(type, element, className, attrName) {
            var i, amountElm = element.length;

            for (var i = amountElm - 1; i >= 0; i--) {

                switch(type) {
                    case'add':
                        $(element[i]).addClass(className[i]);
                    break;
                    case'remove':
                        $(element[i]).removeClass(className[i]);
                    break;
                    case'attr':
                        $(element[i]).attr(attrName[i], className[i]);
                    break;
                }
            };
        },
        
        closeModal: function() {
            var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
                _this = this;

            // Handle any cleanup for the previously set content for the modal
            this.send('modalWillTransition');

            $('.modal-fullscreen-background').one(animationEnd, function(){
                // Finally clear the outlet
                _this.disconnectOutlet({
                    outlet: 'modalContainer',
                    parentView: 'application'
                });
            });

            this.send('scrollEnable');

            $('.modal-fullscreen-background').addClass('is-inactive');
        },

        scrollDisable: function() {
            var $body = $('#site');
            var oldWidth = $body.innerWidth();
            $body.width(oldWidth);
            $('body').addClass('is-stopped-scrolling');
        },

        scrollEnable: function() {
            $('body').removeClass('is-stopped-scrolling');
            $('#site').width("auto");
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
            this.send('modalWillTransition', name, 'modalBack', context);

            // add class flipped and reset default state
            this.send('addRemoveClass', 'attr', ['#card', '.front', '.back'], ['flipped', 'front', 'back'], ['class', 'class', 'class']);
        },

        modalFlipBack: function(name, context) {            
            // Handle any cleanup for the previously set content for the modal
            this.send('modalWillTransition', name, 'modalFront', context);

            $('#card').removeClass('flipped');
        },

        modalSlide: function(name, context) {
            // Handle any cleanup for the previously set content for the modal
            this.send('modalWillTransition', name, 'modalBack', context);

            this.send('addRemoveClass', 'remove', ['.front', '.back'], ['slide-in-left', 'slide-out-right']);
            this.send('addRemoveClass', 'add', ['.front', '.back'], ['slide-out-left', 'slide-in-right']);
        },

        modalSlideBack: function(name, context) {
            // Handle any cleanup for the previously set content for the modal
            this.send('modalWillTransition', name, 'modalFront', context);
            this.send('addRemoveClass', 'remove', ['.front', '.back'], ['slide-out-left', 'slide-in-right']);
            this.send('addRemoveClass', 'add', ['.front', '.back'], ['slide-in-left', 'slide-out-right']);
        },

        modalScale: function(name, context) {
            // Handle any cleanup for the previously set content for the modal
            this.send('modalWillTransition', name, 'modalBack', context);
            this.send('addRemoveClass', 'remove', ['.front', '.back'], ['scale-down', 'scale-up']);
            this.send('addRemoveClass', 'add', ['.front', '.back'], ['scale-back', 'scale-down']);
        },

        modalScaleBack: function(name, context) {
            this.send('modalWillTransition', name, 'modalFront', context);
            this.send('addRemoveClass', 'remove', ['.front', '.back'], ['scale-back', 'scale-down']);
            this.send('addRemoveClass', 'add', ['.front', '.back'], ['scale-down', 'scale-up']);
        },

        modalError: function() {
            var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
                cardSide = $('#card.flipped'),
                container;

            if (Ember.isEmpty(cardSide)) {
                // Front side is showing 
                container = $('#card .front .modal-fullscreen-item');
            } else {
                // If cardSide is defined then it is the flipped/back side
                container = cardSide.find('.modal-fullscreen-item');
            }

            container.addClass('is-shake').one(animationEnd, function(){
                container.removeClass('is-shake');
            });
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