App.Slide = DS.Model.extend({
    url: 'banners',

    title: DS.attr('string'),
    body: DS.attr('string'),
    image: DS.attr('string'),
    background_image: DS.attr('string'),
    video: DS.attr('string'),
    video_url: DS.attr('string'),

    language: DS.attr('string'),

    sequence: DS.attr('number'),
    style: DS.attr('string'),
    tab_text: DS.attr('string'),
    link_text: DS.attr('string'),
    link_url: DS.attr('string'),
    isFirst: function() {
        return (this.get('sequence') == 1);
    }.property('sequence'),

    backgroundStyle: function(){
        var bg = this.get('background_image');
        if (bg) {
            return "background-image: url('" + bg + "');"
        }
        return '';
    }.property('background_image'),

    videoSrc: function(){
        var url = this.get('video_url');
        url = url.replace('http:', '');
        return url + "?api=1&player_id=brand-video&title=0&amp;byline=0&amp;portrait=0&amp;color=00c051"
    }.property('video_url')
});
