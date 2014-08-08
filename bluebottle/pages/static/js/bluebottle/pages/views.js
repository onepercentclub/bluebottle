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

    videoClick: function(evt) {
        var $target = $(evt.target),
            iframe = $('#brand-video'),
            player = $f(iframe),
            animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd';

        if ($target.hasClass('video-play-btn')) {
            $(".video-item").removeClass("is-inactive");
            $(".video-item").addClass("is-active");
            player.api("play");
        }

        if ($target.hasClass('close-video')) {
            $(".video-item").removeClass("is-active");
            $(".video-item").addClass("is-inactive");
            player.api("pause");

            $('.video-item').one(animationEnd, function(){
                $(".video-item").removeClass("is-inactive");
            });

        }

        function onFinish(id) {
            $(".video-item").removeClass("is-active");
            $(".video-item").addClass("is-inactive");

            $('.video-item').one(animationEnd, function(){
                $(".video-item").removeClass("is-inactive");
            });
        }
        
        player.addEvent('ready', function() {
            player.addEvent('finish', onFinish);
        });
        
    }.on('click'),

    linkClick: function (linkEvt) {
        var $target = $(linkEvt.target);

        if ($target.data('emberLinkTo')) {
            var newRoute = $target.data('emberLinkTo'),
                newRouteAttr = $target.data('emberLinkToArg'),
                router = this.get('controller.target.router');

            router.transitionTo(newRoute, newRouteAttr);
        }
    }.on('click'),

    didInsertElement: function(evt) {
        this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });
    }
});


