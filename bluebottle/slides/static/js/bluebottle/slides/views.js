
App.SlideListView = Ember.View.extend({
    templateName: 'slide_list',

    didInsertElement: function() {

        // Carousel
        this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });

        setTimeout(function() {
            $(".home-carousel .carousel-nav li:first-child").addClass("is-active");
        }, 200);
        
    }
});
