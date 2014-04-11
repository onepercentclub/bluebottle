App.BbFlashComponent = Em.Component.extend({

});

App.BbFormFieldComponent = Em.Component.extend({

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
    accept: 'image/*',
    buttonLabel: 'Upload image'
});

App.BbUploadImageAreaComponent = App.BbFormFieldComponent.extend({
    accept: 'image/*',
    buttonLabel: 'Upload image',
    didInsertElement: function() {
    	var file_input = this.$("input[type=file]");
    	file_input.hide();
    	this.$(".image-upload-controls-browse").click(function() {
    		file_input.trigger("click");
    	});
    },
});

App.BbUploadFileAreaComponent = App.BbFormFieldComponent.extend({
    accept: '*/*',
    buttonLabel: 'Upload file',
    didInsertElement: function() {
    	var file_input = this.$("input[type=file]");
    	file_input.hide();
    	this.$(".upload").click(function() {
    		file_input.trigger("click");
    	});
    },
});

App.BbVideoLinkComponent = App.BbTextFieldComponent.extend({
});

App.BbRadioComponent = App.BbFormFieldComponent.extend({
    type: 'radio'
});

App.BbSelectComponent = App.BbFormFieldComponent.extend({

});
