BB = {};

BB.ModalMixin = Em.Mixin.create({
    actions: {
        createUser: function() {
            debugger
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
            this.openInBox(name, context, type, callback);
        },
        
        closeAllModals: function() {
            var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd';
            $('.modal-fullscreen-background').one(animationEnd, function(){
                $('.modal-fullscreen-background').removeClass('is-active');
                $('.modal-fullscreen-background').removeClass('is-inactive');
            });
            $('.modal-fullscreen-background').addClass('is-inactive');
        },

        modalFlip: function(name) {
            this.render(name, {
                outlet: 'modalBack',
                into: 'modalContainer',
            });
            $('#card').addClass('flipped');
        }
    },

    // Add openInBox as function on ApplicationRoute so that it can be used
    // outside the usual template/action context
    openInBox: function(name, context, type, callback) {
        this.render('modalContainer', {
            into: 'application'
        });

        this.render(name, {
            outlet: 'modalFront',
            into: 'modalContainer',
        });

        // var modalPaneTemplate = ['{{view view.bodyViewClass}}'].join("\n");

        // var options = {
        //     classNames: classNames,
        //     defaultTemplate: Em.Handlebars.compile(modalPaneTemplate),
        //     bodyViewClass: view
        // }

        // if (callback) {
        //     options.callback = callback;
        // }

        // Bootstrap.ModalPane.popup(options);
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