
/*
 Views
 */

App.TaskListView = Em.View.extend(App.ScrollInView, {
    templateName: 'task_list'
});

App.TaskPreviewView = Em.View.extend({
    templateName: 'task_preview'
});

App.TaskSummaryView = Em.View.extend({
    templateName: 'task_summary'
});

App.ProjectTaskListView = Em.View.extend(App.ScrollInView, {});


App.TaskMenuView = Em.View.extend({
    templateName: 'task_menu',
    tagName: 'form'
});

App.TaskSearchView = Em.TextField.extend({
    placeholder: gettext('Search')
});


App.TaskNewView = Em.View.extend(App.ScrollInView, {
    templateName: 'task_new',

    submit: function(e) {
        e.preventDefault();
        this.get('controller').createTask();
    }
});


App.TaskEditView = Em.View.extend(App.ScrollInView, {
    templateName: 'task_edit',

    submit: function(e) {
        e.preventDefault();
        this.get('controller').updateTask();
    }
});


App.TaskMemberEdit = Em.View.extend({
    templateName: 'task_member_edit',
    tagName: 'form',

    submit: function(e) {
        e.preventDefault();
        this.get('controller').updateTaskMember();
    }
});

App.TaskMemberApplyView = Em.View.extend({
    templateName: 'task_member_apply',
    tagName: 'form',
    motivation: ''
});


App.TaskFileNewView = Em.View.extend({
    templateName: 'task_file_new',
    tagName: 'form',

    submit: function(){
        e.preventDefault();
        this.get('controller').uploadTaskFile();
    },

    addFile: function(e) {
        e.preventDefault();
        this.get('controller').uploadTaskFile();
    }
});


App.TaskDeadLineDatePicker = App.DatePicker.extend({
    config: {minDate: 0, maxDate: "+1Y"}
});

/*
 Form Elements
 */
App.TaskStatusList = [
    {value: 'open', title: gettext("Open")},
    {value: 'in progress', title: gettext("Running")},
    {value: 'realized', title: gettext("Realised")}
];

App.TaskStatusSelectView = Em.Select.extend({
    content: App.TaskStatusList,
    optionValuePath: "content.value",
    optionLabelPath: "content.title",
    prompt: gettext("Any Status")

});


App.SkillSelectView = Em.Select.extend({
    optionValuePath: "content",
    optionLabelPath: "content.name",
    prompt: gettext("Pick a Skill")
});


App.UsedSkillSelectView = App.SkillSelectView.extend();


App.TaskMemberView = Ember.View.extend({
    templateName: 'task_member'
});