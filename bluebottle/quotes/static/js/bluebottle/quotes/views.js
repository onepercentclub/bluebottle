App.QuoteListView = Ember.View.extend({
    templateName: 'quote_list',

    didInsertElement: function() {
        var controller = this.get('controller');
        this.initQuoteCycle();
    },

    initQuoteCycle: function() {
        var controller = this.get('controller');
        var view = this;

	var set_quote_index = function(){

	    var quote_length = controller.get('quotes').get('length');
	    
	    if (controller.get('quoteIndex') === quote_length) {
                controller.set('quoteIndex', 0);
            }

	    if (controller.get('quoteIndex') + 1 < quote_length){
			controller.set('nextQuoteIndex', controller.get('quoteIndex') + 1);
	    } else{
			controller.set('nextQuoteIndex', 0);
	    }
	}

	controller.set('quoteIndex', 0);
	set_quote_index();

	//Hide the transition quote container
	$('#quote-b').animate({width:'toggle'},0);

	view.swapQuote();

        var quoteIntervalId = setInterval(function() {
            controller.incrementProperty('quoteIndex');
	    
            set_quote_index();
	    
            view.swapQuote();

        }, 6000);

        view.set('quoteIntervalId', quoteIntervalId);
	
    },

    //Function that swaps the quotes using transitions
    swapQuote: function(){

	var controller = this.get('controller');

	//The slide holding the quote
	var quoteHolder = $('#quote-a');
	//The transition slide
	var nextQuoteHolder = $('#quote-b');
	
	var quote = controller.get('quotes').objectAt(controller.get('quoteIndex'));
	var nextQuote = controller.get('quotes').objectAt(controller.get('nextQuoteIndex'));

	var duration = 500;

	//Function that is called once the transition slide is in place
	//This function only sets the content of the quote slide to be
	//the same as of the transition slide and puts the slides back in
	//place for the next transition
	var callback = function(){
	    
	    controller.set('quote',quote);

	    quoteHolder.animate({opacity:'toggle'},0);
	    quoteHolder.animate({'margin-left':'0px'},0);
	    nextQuoteHolder.animate({width:'toggle'},0);
	}

	//Update the contents of the transition slide
        controller.set('next_quote', quote);

	//Slide the ould content out
	quoteHolder.animate({'margin-left':'+=1200'},duration,
			   function(){
			       //Hide the quote slide to provide space to the
			       //transition slide
			       quoteHolder.animate({opacity:'toggle'},0);

			       //Slide in the transition slide
			       nextQuoteHolder.animate({width:'toggle'},duration,callback);});

    },

    willDestroyElement: function() {
        clearInterval(this.get('quoteIntervalId'));
        this.set('quoteIntervalId', null);
    }
});
