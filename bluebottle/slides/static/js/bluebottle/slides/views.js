
App.SlideListView = Ember.View.extend({
    templateName: 'slide_list',

    didInsertElement: function() {

        // Carousel
        this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });
        
        $(".home-carousel .carousel-nav li:first-child").addClass("is-active");
        
    }
});
