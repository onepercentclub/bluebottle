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

// TODO: do we need this goTo code in the ApplicationView
//       we have it in App.GoTo
App.ApplicationView = Em.View.extend({
    elementId: 'site',
    click: function(e) {
        var $target = $(e.target);
        if ($target.hasClass('goto')) {
            var anchor = $target.data('target') || $target.attr('rel');
            if (anchor) {
                this.send('goTo', anchor);
                e.preventDefault();
            }
        }
    },

    isTouch: function() {
        var isTouch = ('ontouchstart' in document.documentElement);
        return isTouch;
    },

    addTouch: function(element) {
        if (this.isTouch()) {
            $('body').addClass('touch');
        }
        else {
            $('body').addClass('no-touch');
        };
    }.on('didInsertElement'),

    touchProfileMenu: function() {
        if (this.isTouch()) {
            var navMember = $('.nav-member');
            navMember.addClass('touch');
            
            navMember.on('click', function(e) {
                e.preventDefault();
                navMember.toggleClass('is-active');
            });
        }
    }.on('didInsertElement')
});

// Extend from this class to allow auto focus first input in form
// and pressing 'enter' in one of the form inputs will submit the 
// form (action) if the 'submitAction' property has been defined.
// TODO: make this a mixin and/or component.
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
            
            var action = this.get('submitAction');
            if (Em.typeOf(action) == 'string' && action.length) {
                this.get('controller').send(action);
            }
        }
    }
});

App.RadioButton = Em.View.extend({
    tagName : 'input',
    type : 'radio',
    attributeBindings : [ 'name', 'type', 'value', 'checked:checked:', 'id' ],

    click : function() {
        this.set('selection', this.$().val())
    },

    checked : function() {
        return this.get('value') == this.get('selection');
    }.property('selection')
});
