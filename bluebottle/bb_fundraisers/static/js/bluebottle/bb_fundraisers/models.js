App.Adapter.map('App.Fundraiser', {
    owner: {embedded: 'load'}
});

App.Fundraiser = DS.Model.extend({
    url: 'fundraisers',

    project: DS.belongsTo('App.ProjectPreview'),
    owner: DS.belongsTo('App.UserPreview'),

    title: DS.attr('string'),
    description: DS.attr('string'),

    // Media
    image: DS.attr('image'),
    video_url: DS.attr('string', {defaultValue: ''}),
    video_html: DS.attr('string'),

    amount: DS.attr('number'),
    amount_donated: DS.attr('number'),
    deadline: DS.attr('date'),

    amount_needed: function() {
        var donated = this.get('amount') - this.get('amount_donated');
        if(donated < 0) {
            return 0;
        }
        return Math.ceil(donated);
    }.property('amount', 'amount_donated'),

    is_funded: function() {
        return this.get('amount_needed') <= 0;
    }.property('amount_needed'),

    overDeadline: function() {
        var now = new Date();
        return now > this.get("deadline");
    }.property('deadline'),

    daysToGo: function(){
        var now = new Date();
        var microseconds = this.get('deadline').getTime() - now.getTime();
        return Math.ceil(microseconds / (1000 * 60 * 60 * 24));
    }.property('deadline'),

    getImage: function(){
        if (this.get('image')) {
            return this.get('image.square')
        }
        return STATIC_URL + 'images/fundraisers/default-picture.png'
    }.property('image'),

    maxDate: function(){
        var deadline = this.get('project.deadline'),
            now = new Date();
        if (deadline) {
            return '+' + parseInt((deadline.getTime() - now)/(24*3600*1000)) + 'd';
        }
    }.property('project.deadline')
});
