/* Embedded properties */

App.Adapter.map('App.Project', {
    owner: {embedded: 'load'},
    country: {embedded: 'load'},
    meta_data: {embedded: 'load'},
    tags: {embedded: 'load'}
});

App.Adapter.map('App.ProjectPreview', {
    owner: {embedded: 'load'},
    country: {embedded: 'load'},
    theme: {embedded: 'load'}
});

App.Adapter.map('App.MyProject', {
    tags: {embedded: 'always'}
});

/* Models */

App.ProjectCountry = DS.Model.extend({
    name: DS.attr('string'),
    subregion: DS.attr('string')
});


App.Project = DS.Model.extend({
    url: 'bb_projects/projects',

    // Model fields
    slug: DS.attr('string'),
    status: DS.belongsTo('App.ProjectPhase'),
    created: DS.attr('date'),

    owner: DS.belongsTo('App.UserPreview'),

    // Start
    language: DS.belongsTo('App.Language'),

    // Pitch
    title: DS.attr('string'),
    pitch: DS.attr('string'),
    theme: DS.belongsTo('App.Theme'),
    tags: DS.hasMany('App.Tag'),

    // Story
    description: DS.attr('string'),
    effects: DS.attr('string'),
    reach: DS.attr('number'),

    // new story field
    story: DS.attr('string'),

    // Location
    country: DS.belongsTo('App.Country'),
    latitude: DS.attr('string'),
    longitude: DS.attr('string'),

    // Media
    image: DS.attr('image'),
    video_url: DS.attr('string'),
    video_html: DS.attr('string'),

    // Money
    amount_asked: DS.attr('number'),
    amount_donated: DS.attr('number'),
    amount_needed: DS.attr('number'),
    deadline: DS.attr('date'),

    viewable: DS.attr('boolean'),
    editable: DS.attr('boolean'),

    organization: DS.belongsTo("App.Organization"),

    phaseName: function(){
        return this.get('status').get('name');
    }.property('phaseName'),

    phaseNum: function(){
        if (this.get('status') == null){
            return 1;
        }
        return this.get('status.sequence');
    }.property('status.sequence'),

    isStatusPlan: Em.computed.lt('phaseNum', 4),

    isStatusPlanNew: Em.computed.equal('phaseNum', 1),

    isStatusNeedsWork: Em.computed.equal('phaseNum', 3),

    isStatusCampaign: Em.computed.equal('phaseNum', 4),

    isStatusCompleted: Em.computed.equal('phaseNum', 5),

    isStatusStopped: Em.computed.gt('phaseNum', 6),

    is_funded: Em.computed.lte('amount_needed', 0),

    hasTasks: Em.computed.gte('task_count', 0),

    isSupportable: function () {
        var now = new Date();
        // Look if Project is in Capaign phase, asked for money and is bfeore deadline.
        return this.get('isStatusCampaign') && this.get('amount_asked') && this.get('deadline') > now;
    }.property('isStatusCampaign', 'deadline', 'amount_asked'),

    getProject: function(){
        return App.Project.find(this.get('id'));
    }.property('id'),

    //those two function are based on fields which are not implemented here
    //they shouldn't be here, or deadline should be here
    daysToGo: function(){
        if (!this.get('deadline')) {
            return null;
        }
        var now = new Date();
        var microseconds = this.get('deadline').getTime() - now.getTime();
        return Math.ceil(microseconds / (1000 * 60 * 60 * 24));
    }.property('deadline'),

    overDeadline: function() {
        var now = new Date();
        return now > this.get("deadline");
    }.property('deadline'),

    cleanTags: function(){
        // Ugly fix to avoid putting tags
        this.get('tags').forEach(function (tag) {
            if (tag.get('isDirty')){
                tag.transitionTo('loaded.updated.saved');
            }
        });
    }.observes('isDirty')
});


App.ProjectPhase = DS.Model.extend({
    url: 'bb_projects/phases',
    name: DS.attr('string'),
    description: DS.attr('string'),
    sequence: DS.attr('number'),
    active: DS.attr('boolean'),
    editable: DS.attr('boolean'),
    viewable: DS.attr('boolean'),
    ownerEditable: DS.attr('boolean')
});

App.ProjectPreview = App.Project.extend({
    url: 'bb_projects/previews',
    owner: DS.belongsTo('App.UserPreview'),
    image: DS.attr('string'),
    country: DS.belongsTo('App.ProjectCountry'),
    pitch: DS.attr('string'),
    theme: DS.belongsTo('App.Theme')
});


App.ProjectSearch = DS.Model.extend({

    text: DS.attr('string'),
    country: DS.attr('number'),
    theme:  DS.attr('number'),
    ordering: DS.attr('string', {defaultValue: 'popularity'}),
    status: DS.attr('number', {defaultValue: 5}),
    page: DS.attr('number', {defaultValue: 1})

});


App.Theme = DS.Model.extend({
    url: 'bb_projects/themes',
    name: DS.attr('string')
});


App.UsedTheme = App.Theme.extend({
    url: 'bb_projects/used_themes'
});

/* Project Manage Models */

App.MyProjectBudgetLine = DS.Model.extend({
    url: 'bb_projects/budgetlines/manage',

    project: DS.belongsTo('App.MyProject'),
    description: DS.attr('string'),
    amount: DS.attr('number')
});


App.BudgetLine = DS.Model.extend({
    project: DS.belongsTo('App.Project'),
    description: DS.attr('string'),
    amount: DS.attr('number')
});


App.MyProject = App.Project.extend(App.ModelValidationMixin, {
    url: 'bb_projects/manage',
    
    requiredStoryFields: ['description', 'reach'],
    requiredPitchFields: ['validTitle', 'pitch', 'theme', 'tags.length', 'country', 'latitude', 'longitude'],
    friendlyFieldNames: {
        validTitle: gettext('Title')
    },

    init: function () {
        this._super();

        this.validatedFieldsProperty('validStory', this.get('requiredStoryFields'));
        this.validatedFieldsProperty('validPitch', this.get('requiredPitchFields'));

        this.missingFieldsProperty('missingFieldsStory', this.get('requiredStoryFields'));
        this.missingFieldsProperty('missingFieldsPitch', this.get('requiredPitchFields'));
    },

    save: function () {
        this.one('becameInvalid', function(record) {
            // Ember-data currently has no clear way of dealing with the state
            // loaded.created.invalid on server side validation, so we transition
            // to the uncommitted state to allow resubmission
            if (record.get('isNew')) {
                record.transitionTo('loaded.created.uncommitted');
            } else {
                record.transitionTo('loaded.updated.uncommitted');
            }
        });

        this._super();
    },

    validTitle: function () {
        // Valid title if it has a length and there are no api errors for the title.
        return this.get('title.length') && !this.get('errors.title');
    }.property('title.length', 'errors.title'),

    valid: function(){
        return (this.get('validStory') && this.get('validPitch'));
    }.property('validStory', 'validPitch'),

    organization: DS.belongsTo('App.MyOrganization'),
    currentUser: DS.belongsTo('App.CurrentUser'),

    canSubmit: function(){
        if (!this.get('status')) {
            return true;
        }
        if (this.get('isStatusPlanNew')) {
            return true;
        }
        if (this.get('isStatusNeedsWork')) {
            return true;
        }
        return false;
    }.property('status')

});
