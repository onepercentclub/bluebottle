(function() {

var jQuery;

if (window.jQuery === undefined || window.jQuery.fn.jquery !== '1.11.1') {
	var script_tag = document.createElement('script');
	script_tag.setAttribute("type", "text/javascript");
	script_tag.setAttribute("src", "http://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js");

	if (script_tag.readyState) {
		script_tag.onreadystatechange = function (){ //Specific for old versions of IE
			if (this.readyState == 'complete' || this.readyState == 'loaded') {
				scriptLoadHandler();
			}
		};
	} else { //Other browsers use this
		script_tag.onload = scriptLoadHandler;
	}

	(document.getElementsByTagName("head")[0] || document.documentElement).appendChild(script_tag);
} else {
	jQuery = window.jQuery;
	main();
}

function scriptLoadHandler() {
	jQuery = window.jQuery.noConflict(true);
	main();
}

function main(){
	jQuery(document).ready(function($){

		var el = $('div#widget-container');
		var id = $(el).data('id')
		var width = $(el).data('width') ? $(el).data('width') : 100;
		var height = $(el).data('height') ? $(el).data('height') : 80;
		var partner = $(el).data('partner')
		var language = $(el).data('language') ? $(el).data('language') : 'en';

		var jsonp_url = "http://localhost:8000/embed?callback=?&id=" + id + "&width=" + width + "&height=" + height +"&partner=" + partner + '&language=' + language;
		$.getJSON(jsonp_url, function(data){
			$('#widget-container').html(data.html);
		});

	});
}

})();
