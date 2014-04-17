App.BbFlashComponent = Em.Component.extend({

});

App.BbFormFieldComponent = Em.Component.extend({

});

App.BbTextFieldComponent = App.BbFormFieldComponent.extend({
    type: 'text'
});

App.BbTextAreaComponent = App.BbFormFieldComponent.extend({

  didInsertElement: function(){
    var el = this.$('textarea.redactor');
    var view = this;
    $(el).redactor({
        blurCallback: function(e){
            $(el).val(view.$('.redactor').redactor('get'));
            $(el).trigger('change');
        }
    });
    $(el).redactor('insertHtml', view.get('value'));
  }
});

App.BbMapPickerComponent = App.BbFormFieldComponent.extend({
});

App.BbDatePickerComponent = App.BbFormFieldComponent.extend({
});

App.BbDatePickerSliderComponent = App.BbFormFieldComponent.extend({
});



App.BbUploadImageComponent = App.BbFormFieldComponent.extend({
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
