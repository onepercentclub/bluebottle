/**
 * Embedded mappings
 */

App.Adapter.map('App.Task', {
    author: {embedded: 'load'},
    tags: {embedded: 'always'},
    members: {embedded: 'load'},
    files: {embedded: 'load'}
});
App.Adapter.map('App.TaskPreview', {
    author: {embedded: 'load'},
    project: {embedded: 'load'}
});
App.Adapter.map('App.TaskMember', {
    member: {embedded: 'load'}
    //task: {embedded: 'load'}
});
App.Adapter.map('App.MyTaskMember', {
    member: {embedded: 'load'},
    task: {embedded: 'load'}
});
App.Adapter.map('App.TaskFile', {
    author: {embedded: 'load'}
});


/*
 Models
 */

App.TaskMember = DS.Model.extend({
    url: 'bb_tasks/members',

    member: DS.belongsTo('App.UserPreview'),
    created: DS.attr('date'),
    status: DS.attr('string', {defaultValue: 'applied'}),
    motivation: DS.attr('string'),
    task: DS.belongsTo('App.Task'),

    isStatusApplied: function(){
        return (this.get('status') == 'applied');
    }.property('status'),

    isStatusAccepted: function(){
        return (this.get('status') == 'accepted');
    }.property('status'),

    isStatusRejected: function(){
        return (this.get('status') == 'rejected');
    }.property('status'),

    isStatusRealized: function(){
        return (this.get('status') == 'realized');
    }.property('status'),

    isAccepted: function(){
        return (this.get('isStatusAccepted') || this.get('isStatusRealized'));
    }.property('status'),

    // Return individual labels here so they're added to translations.
    statusLabel: function(){
        var status = this.get('status');
        switch (status) {
            case 'applied':
                return gettext('applied for');
                break;
            case 'rejected':
                return gettext('was rejected for');
                break;
            case 'accepted':
                return gettext('was accepted for');
                break;
            case 'realized':
                return gettext('realised');
                break;
            case 'stopped':
                return gettext('withdrew from');
                break;
            default:
                Em.Logger.error('Task status not found: ' + status);
                return status;
        }

    }.property('status')


});

App.MyTaskMember = App.TaskMember.extend({
    url: 'bb_tasks/members/my-task',

    task: DS.belongsTo('App.TaskPreview'),
    time_spent: DS.attr('number')
    // TODO: validation, time_spent can't be greater than 8
});

App.TaskFile = DS.Model.extend({
    url: 'bb_tasks/files',

    author: DS.belongsTo('App.UserPreview'),
    title: DS.attr('string'),
    created: DS.attr('date'),
    file: DS.attr('file'),
    task: DS.belongsTo('App.Task')
});

App.Task = DS.Model.extend({
    url: 'bb_tasks',

    // Model fields
    author: DS.belongsTo('App.UserPreview'),
    title: DS.attr('string'),
    description: DS.attr('string'),
    end_goal: DS.attr('string'),
    created: DS.attr('date'),
    deadline: DS.attr('date'),
    project: DS.belongsTo('App.Project'),
    members: DS.hasMany('App.TaskMember'),
    files: DS.hasMany('App.TaskFile'),
    skill: DS.belongsTo('App.Skill'),
    // NOTE: it really is a number, but this allows us to use proper server side validation
    people_needed: DS.attr('string', {defaultValue: '1'}),
    location: DS.attr('string', {defaultValue: ''}),
    time_needed: DS.attr('number'),
    status: DS.attr('string', {defaultValue: 'open'}),
    tags: DS.hasMany('App.Tag'),

    tags_list: function() {
    	var arr = [];
        this.get('tags').forEach(function (item, index, self) {
            arr.push(item.get('id'));
        });
        return arr.join(', ');
    }.property('tags.@each.id'),

    // Calculate status booleans here so we can use it in all views
    isStatusOpen: function(){
        return this.get('status') == 'open';
    }.property('status'),

    isStatusInProgress: function(){
        return this.get('status') == 'in progress';
    }.property('status'),

    isStatusClosed: function(){
        return this.get('status') == 'closed';
    }.property('status'),

	// statusRealized is not working, instead we have completed...
    isStatusRealized: function(){
        return this.get('status') == 'realized';
    }.property('status'),

	isStatusCompleted: function(){
        return this.get('status') == 'completed';
    }.property('status'),

    ////
    // Override this function to change what determines an available task
    isAvailable: function () {
        var now = new Date();
        return this.get('isStatusOpen') && this.get('deadline') > now;
    }.property('isStatusOpen', 'deadline'),

    isUnavailable: function () {
        return !this.get('isAvailable');
    }.property('isAvailable'),

    membersCount: function() {
        return this.get('members').filterBy('isStatusAccepted', true).length;
    }.property("members.@each"),

    membersNeeded: function() {
        return this.get("people_needed") - this.get('members').filterBy('isStatusAccepted', true).length;
    }.property('people_needed', 'members.@each'),
    
	hasMoreThanOneMember: function() {
        return this.get('membersCount') > 1
    }.property('membersCount'),
    
    hasMembers: function() {
        return this.get('members.length') > 0;
    }.property("members.length"),

    moreThanOnePersonNeeded: function() {
        return this.get("people_needed") > 1
    }.property("people_needed"),

    acceptedMemberCount: function(){
        return (this.get('members').filterBy('isAccepted').get('length'));
    }.property('model.members.@each.status'),

    timeNeeded: function(){
        var times = App.TimeNeededList;
        var hours = this.get('time_needed');
        for (time in times) {
            if (times[time].value == hours) {
                return times[time].title;
            }
        }
        return hours + ' hours';
    }.property('time_needed'),

    image: function(){
        return this.get('project.image.small');
    }.property('project.image'),

    maxDate: function(){
        if (!this.get('project.deadline')) {
            return null;
        }
        return '+' + this.get('project.daysToGo') + 'd';
    }.property('project.deadline'),

    daysToGo: function(){
        if (!this.get('deadline')) {
            return null;
        }
        var now = new Date();
        var microseconds = this.get('deadline').getTime() - now.getTime();
        return Math.ceil(microseconds / (1000 * 60 * 60 * 24));
    }.property('deadline'),

    // Return individual labels here so they're added to translations.
    statusLabel: function(){
        var status = this.get('status');
        switch (status) {
            case 'open':
                return gettext('open');
                break;
            case 'in progress':
                return gettext('in progress');
                break;
            case 'realized':
                return gettext('realised');
                break;
            case 'closed':
                return gettext('closed');
                break;
            default:
                Em.Logger.error('Task status not found: ' + status);
                return status;
        }

    }.property('status')

});

App.NewTask = App.Task.extend({
    project: DS.belongsTo('App.Project')
});


App.Skill = DS.Model.extend({
    url: 'bb_tasks/skills',
    name: DS.attr('string')
});


// model for the skills effectively coupled with a task
App.UsedSkill = App.Skill.extend({
    url: 'bb_tasks/used_skills'
});


/*
Preview model that doesn't contain all the properties.
 */
App.TaskPreview = App.Task.extend({
    url: 'bb_tasks/previews',
    project: DS.belongsTo('App.ProjectPreview'),

    image: function(){
        return this.get('project.image');
    }.property('project.image')
});


App.TaskSearch = DS.Model.extend({
    text: DS.attr('string'),
    skill: DS.attr('string'),
    ordering: DS.attr('string', {defaultValue: 'newest'}),
    status: DS.attr('string', {defaultValue: 'open'}),
    page: DS.attr('number', {defaultValue: 1})

});
