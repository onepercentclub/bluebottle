BB = {};

BB.ModalControllerMixin = Em.Mixin.create({
    actions: {
        close: function () {
            this.send('closeModal');
        }
    }
})

BB.ModalMixin = Em.Mixin.create({
    actions: {
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
            this.render('modalContainer', {
                into: 'application',
                outlet: 'modalContainer',
                controller: this.controllerFor('modalContainer')
            });

            return this.render(name, {
                into: 'modalContainer',
                outlet: 'modalFront',
                controller: this.controllerFor(name)
            });
        },
        
        closeModal: function() {
            var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
                _this = this;

            $('.modal-fullscreen-background').one(animationEnd, function(){
                // Finally clear the outlet
                _this.disconnectOutlet({
                    outlet: 'modalContainer',
                    parentView: 'application'
                });
            });

            $('.modal-fullscreen-background').addClass('is-inactive');
        },

        modalFlip: function(name, model) {
            var controller = this.controllerFor(name);

            if (Em.typeOf(model) != 'undefined')
                controller.set('model', model);

            this.render(name, {
                into: 'modalContainer',
                outlet: 'modalBack',
                controller: controller
            });

            $('#card').addClass('flipped');
        }
    },
});

BB.ModalContainerController = Em.ObjectController.extend(BB.ModalControllerMixin, {});

BB.ModalContainerView = Em.View.extend({
    tagName: null,
    template: Ember.Handlebars.compile([
        '<div class="modal-fullscreen-background is-active">',
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