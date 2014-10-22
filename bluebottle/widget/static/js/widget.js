(function() {

    var host = 'http://localhost:8000';
    var jQuery;
    var opcJquery = document.getElementById('onepercentclub-jquery');

    if (opcJquery) {
        return false;
    }

    if (window.jQuery === undefined || window.jQuery.fn.jquery !== '1.11.1') {
        var script_tag = document.createElement('script');

        script_tag.setAttribute('id', 'onepercentclub-jquery');
        script_tag.setAttribute("type", "text/javascript");
        script_tag.setAttribute("src", "//ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js");

        if (script_tag.readyState) {
            script_tag.onreadystatechange = function (){
                // Specific for old versions of IE
                if (this.readyState == 'complete' || this.readyState == 'loaded') {
                    scriptLoadHandler();
                }
            };
        } else {
            // Other browsers use this
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
            // $('.widget-container').each(function(){
            //     var el = $(this);
            //     var project = el.data('project') ? el.data('project') : '';
            //     var size = el.data('size') ? el.data('size') : 'default';
            //     var width = el.data('width') ? el.data('width') : 300;
            //     var height = el.data('height') ? el.data('height') : 300;
            //     var partner = el.data('partner') ? el.data('partner') : '';
            //     var language = el.data('language') ? el.data('language') : 'en';
            //     var jsonp_url = host + "/embed?callback=?&project=" + project + "&size=" + size + "&width=" + width + "&height=" + height +"&partner=" + partner + '&language=' + language;
            //     $.getJSON(jsonp_url, function(data){
            //         el.html(data.html);
            //     });
            // });
            $('script[data-id="opcwidget"]').each(function() {
                var el = $(this);
                var _this = this;

                var project = $(this).data('project') ? $(this).data('project') : '';
                var size = $(this).data('size') ? $(this).data('size') : 'default';
                var width = $(this).data('width') ? $(this).data('width') : 300;
                var height = $(this).data('height') ? $(this).data('height') : 300;
                var partner = $(this).data('partner') ? $(this).data('partner') : '';
                var language = $(this).data('language') ? $(this).data('language') : 'en';
                var jsonp_url = host + "/embed?callback=?&project=" + project + "&size=" + size + "&width=" + width + "&height=" + height +"&partner=" + partner + '&language=' + language;
                $.getJSON(jsonp_url, function(data){
                    console.log(data)
                    $(_this).after(data.html);
                });
                
            });
        });
    }

})();
