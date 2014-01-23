
App.SlideListView = Ember.View.extend({
    templateName: 'slide_list',

    didInsertElement: function() {

        // Carousel
        this.$().find('.carousel').unslider({
            dots: true,
            fluid: true,
            delay: 10000
        });
    }
});
