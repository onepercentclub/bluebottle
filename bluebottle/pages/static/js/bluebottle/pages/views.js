/*
   Mixin to enable scrolling from one anchor point to another
   within a same page.

   Mix the mixin into View classes like:
   e.g. App.YourView = Ember.View.extend(App.GoTo, {});

   And, In your template,

   <a class="goto" href="#Destination" data-target="#Destination">Source</a>

   Or,

   <a {{action 'goTo' '#Destination' target="view" bubbles=false}}>Source</a>
 */
App.GoTo = Ember.Mixin.create({

    click: function(e) {
        var $target = $(e.target);
        if ($target.hasClass('goto')) {
            var anchor = $target.data('target') || $target.attr('rel');
            if (anchor) {
                this.goTo(anchor);
                e.preventDefault();
            }
        }
    },

    goTo: function(target) {
        $('html, body').stop().animate({
            scrollTop: $(target).offset().top - $('#header').height()
        }, 500);
    }
});


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

    didInsertElement: function(e){
		this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });
    }
});
