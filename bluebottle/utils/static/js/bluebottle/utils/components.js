
App.BbFormFieldComponent = Em.Component.extend({
    // Variables that should be translated.
    translatable: ['label', 'hint', 'placeholder'],

    didInsertElement: function(){
        var view = this;
        // Translate all translatables.
        this.get('translatable').map(function(param){
            view.set(param, gettext(view.get(param)));
        });
    }
});

App.BbTextFieldComponent = App.BbFormFieldComponent.extend({
    type: 'text'
});

App.BbTextAreaComponent = App.BbFormFieldComponent.extend({
});

App.BbMapPickerComponent = App.BbFormFieldComponent.extend({
});

App.BbDatePickerComponent = App.BbFormFieldComponent.extend({
});

App.BbUploadImageComponent = App.BbFormFieldComponent.extend({
    translatable: ['label', 'hint', 'placeholder', 'buttonLabel'],

    accept: 'image/*',
    buttonLabel: 'Upload image'
});

App.BbVideoLinkComponent = App.BbTextFieldComponent.extend({
});

App.BbRadioComponent = App.BbFormFieldComponent.extend({
    type: 'radio'
});

App.BbSelectComponent = App.BbFormFieldComponent.extend({

});
