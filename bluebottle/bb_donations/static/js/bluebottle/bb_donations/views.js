App.DonationView = App.FormView.extend({
    amount: gettext('Amount'),

  keyDown: function(e){
      var input = this.$().find('.donation-input'),
        inputVal = input.val();
      
      if (inputVal.length > 4) {
        $(input).addClass('is-long');
      } else if (inputVal.length <= 4) {
        $(input).removeClass('is-long');
      }
    } 
});

App.DonationWallPostView = Em.View.extend({
    templateName: 'donation_wall_post',

    didInsertElement: function() {
        var textMax = 140,
            textarea = this.$().find('.wallpost-textarea'),
            countWord = this.$().find('.count-words');

        textarea.on('keyup', function(){
            var textareaLenght = textarea.val().length,
                text_remaining = textMax - textareaLenght,
                total = 140 - text_remaining;

            if (textarea.val() === '') {
                total = '0';
            }

            countWord.html(total);
        });
    }
});

App.DonationSuccessView = Em.View.extend({
    templateName: 'donation_success',
    supported: true,

    backdropStyle: function(){
        return "background: url(" + this.get('controller.project.image.large') + ") no-repeat center top; " +
        "-webkit-background-size: cover; " +
        "-moz-background-size: cover; " +
        "-o-background-size: cover; " +
        "background-size: cover; ";
    }.property('project'),

    didInsertElement: function() {
        if(!document.createElement('svg').getAttributeNS) {
            this.setProperties({
                supported: false
            });
        }
    }
});

App.CanvasView = Em.View.extend({
    tagName: 'canvas',
    elementId: 'confetti-canvas'

});
