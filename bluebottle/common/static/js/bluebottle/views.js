/* Views */

App.ModalContainerView = BB.ModalContainerView.extend();

App.LanguageView = Em.View.extend({
    templateName: 'language',
    classNameBindings: ['isSelected:active'],
    isSelected: function(){
        if (this.get('content.code') == App.language) {
            return true;
        }
        return false;
    }.property('content.code')

});

App.LanguageSwitchView = Em.CollectionView.extend({
    classNames: ['nav-language'],
    content: App.interfaceLanguages,
    itemViewClass: App.LanguageView
});

App.LanguageSelectView = Em.Select.extend({
    classNames: ['language'],
    optionValuePath: 'content.id',
    optionLabelPath: 'content.native_name',
    prompt: gettext('Pick a language')
});

App.ApplicationView = Em.View.extend({
    elementId: 'site'
});

App.FormView = Em.View.extend({
    setFocus: function() {
        var inputs = this.$().find('input');
        if ( inputs.length > 0 ) {
           Ember.run.later(this, function() {
            inputs.first().focus();
           }, 100)
        }
    }.on('didInsertElement'),

    keyPress: function (evt) {
        var code = evt.which;
        // If enter key pressed
        if (code == 13) {
            evt.preventDefault();
            if (!Em.isEmpty(this.submitAction) && Em.typeOf(this.submitAction) == 'string') {
                this.get('controller').send(this.submitAction);
            }
        }
    }
});