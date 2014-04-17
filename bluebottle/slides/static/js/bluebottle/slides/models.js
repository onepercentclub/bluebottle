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
        return (this.get('sequence') == 1);
    }.property('sequence')
});
