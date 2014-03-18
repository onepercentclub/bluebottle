App.MyOrganizationSelectView = Em.Select.extend({
    contentBinding: 'controller.organizations',
    optionValuePath: 'content.id',
    optionLabelPath: 'content.name',
    prompt: gettext('Pick an organization'),
    selectionBinding: 'controller.selectedOrganization'
});