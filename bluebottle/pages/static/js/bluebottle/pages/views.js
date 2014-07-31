App.PageView = Ember.View.extend(App.GoTo, {
    templateName: 'page',

    classNames: 'page static-page'.w(),

    setup: function() {
        Ember.run.scheduleOnce('afterRender', this, function() {
            if (!Em.isNone(this.$())) {
                this.renderSections();
                this.bindEvents();
            }
        });
    }.observes('controller.body'),

    willDestroyElement: function() {
        this.unbindEvents();
    },

    bindEvents: function() {
        $(window).on('resize', $.proxy(this.renderSections, this));
    },

    unbindEvents: function() {
        $(window).off('resize', $.proxy(this.renderSections, this));
    },

    renderSections: function(e) {
        var windowHeight = $(window).height();
        
        this.$('.static-onepage-content').each(function() {
            // Reset first to get correct height
            $(this).css({
                'position' : 'relative',
                'height' : 'auto'
            });
            // Set static height for centering if not higher then section
            if ($(this).height() <= $(window).height() - 100) {
                $(this).css({
                    'height' : $(this).height() + 'px',
                    'position' : 'absolute'
                });
                // Set section height to window height
                $(this).closest( ".static-onepage-section" ).css('height', windowHeight + 'px');
            }
        });
    },

    didInsertElement: function(evt) {
        // Check if the content has any ember link attributes
        // This allows custom page content to specify linkTo targets
        var _this = this;
        this.$('[data-ember-link-to]').on('click', function (linkEvt) {
            var target = $(linkEvt.target),
                newRoute = target.data('emberLinkTo'),
                newRouteAttr = target.data('emberLinkToArg'),
                router = _this.get('controller.target.router');

            router.transitionTo(newRoute, newRouteAttr);
        });

        this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });
    }
});
