App.Slide = DS.Model.extend({
    url: 'banners',

    title: DS.attr('string'),
    body: DS.attr('string'),
    image: DS.attr('string'),
    imageBackground: DS.attr('string'),
    video: DS.attr('string'),

    language: DS.attr('string'),

    sequence: DS.attr('number'),
    style: DS.attr('string'),
    tab_text: DS.attr('string'),
    link_text: DS.attr('string'),
    link_url: DS.attr('string'),
    isFirst: function() {
        var lowestValue = null;
        App.Slide.find().forEach(function(slide) {
            var sequence = slide.get("sequence");
            if(lowestValue == null || sequence < lowestValue)
                lowestValue = sequence;
        });
        return (this.get('sequence') === lowestValue);
    }.property('@each.sequence')
});
