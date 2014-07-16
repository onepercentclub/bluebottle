BB = {};

BB.ModalControllerMixin = Em.Mixin.create({
    // This can be overridden with code to respond with when the 
    // modal content is about to be replaced with new content.
    // This will usually involve clearing the model data => form fields
    willClose: Em.K,

    // This can be overridden with code to respond with when the 
    // modal content is about to be displayed.
    willOpen: Em.K,

    actions: {
        close: function () {
            this.send('closeModal');
        }
    }
});

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

                // Call willOpen on the new modal - if defined
                if (newController && Em.typeOf(newController.willOpen) == 'function')
                    newController.willOpen();

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

            if (Em.isEmpty(type))
                modalContainer.set('type', 'normal');
            else
                modalContainer.set('type', type);

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

            $('.modal-fullscreen-background').removeClass('is-active');
            $('.modal-fullscreen-background').addClass('is-inactive');
        },

        scrollDisable: function() {
            var $body = $('body');
            var oldWidth = $body.innerWidth();
            $body.width(oldWidth);
            $('#header').width(oldWidth);
            $body.addClass('is-stopped-scrolling');
        },

        scrollEnable: function() {
            $('body').removeClass('is-stopped-scrolling');
            $('#header').width('');
            $('body').width('');
        },

        closeKeyModal: function(key) {
            var self = this;
            $(document).on('keydown', function(e) {
                if(e.keyCode == key) {
                    self.send('closeModal');
                }
            });
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
                cardSlide = $('.slide-in-right'),
                container;

            // Either cardSlide or cardSide will be defined if the back side is visible
            // otherwise it must be on the front side.
            if (Ember.isEmpty(cardSide) && Ember.isEmpty(cardSlide)) {
                // Front side is showing 
                container = $('#card .front .modal-fullscreen-item');
            } else {
                container = $('#card .back .modal-fullscreen-item');
            }

            container.addClass('is-shake').one(animationEnd, function(){
                container.removeClass('is-shake');
            });
        }
    },
});

BB.ModalContainerController = Em.ObjectController.extend(BB.ModalControllerMixin, {
    currentController: null,
    type: null
});

BB.ModalContainerView = Em.View.extend(Ember.TargetActionSupport,{
    tagName: null,

    click: function(e) {
        var _this = this,
            string = e.target.className.substring()
            className = string.indexOf("is-active");

        if (className > 0) {
            _this.get('controller').send('closeModal');
        }
    },
    
    template: Ember.Handlebars.compile([
        '<div class="modal-fullscreen-background is-active">',
            '<div {{bindAttr class="type: :modal-fullscreen-container"}}>',
                '<div id="card">',
                    '<div class="front">',
                        '<div class="modal-fullscreen-item">{{outlet "modalFront"}}</div>',
                    '</div>',
                    '<div class="back">',
                        '<div class="modal-fullscreen-item">{{outlet "modalBack"}}</div>',
                    '</div>',
                '</div>',
            '</div>',
        '</div>'].join("\n"))
});