App.MyOrganizationSelectView = Em.Select.extend({
    prompt: gettext('Pick an organization'),

    didInsertElement: function () {
        this.$('option:first').attr('disabled', true);
    }
});