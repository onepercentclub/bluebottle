BB = {};

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
        
        closeAllModals: function() {
            var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd';
            $('.modal-fullscreen-background').one(animationEnd, function(){
                $('.modal-fullscreen-background').removeClass('is-active');
                $('.modal-fullscreen-background').removeClass('is-inactive');
            });
            $('.modal-fullscreen-background').addClass('is-inactive');

            return this.disconnectOutlet({
                outlet: 'modalContainer',
                parentView: 'application'
            });
        },

        modalFlip: function(name) {
            this.render(name, {
                into: 'modalContainer',
                outlet: 'modalBack',
                controller: this.controllerFor(name)
            });
            $('#card').addClass('flipped');
        }
    },
});

BB.ModalContainerController = Em.ObjectController.extend({});

BB.ModalContainerView = Em.View.extend({
	tagName: '',
	template: Ember.Handlebars.compile([
    '<div class="modal-fullscreen-background is-active">',
        '<div class="modal-fullscreen-container">',
        '<div id="card">',
            '<figure class="front">',
                '<div class="modal-fullscreen-item">',
                    '{{outlet "modalFront"}}',
                '</div>',
            '</figure>',
            '<figure class="back">',
                '<div class="modal-fullscreen-item">',
                    '{{outlet "modalBack"}}',
                '</div>',
            '</figure>',
        '</div>',
    '</div>'].join("\n"))
});