function removeRedundantTabs() {
    var t = 0;
    django.jQuery('.changeform-tabs-item:contains("General")').each(function(index, tab){
        t++;
        if (t > 1) {
            tab.remove();
        }
    });
}

function higlightSelectedFilters() {

    django.jQuery('.select2-hidden-accessible').
        find('option:first:selected').
        parent().parent().
        find('.select2-selection__rendered').addClass('select2-selection__placeholder');
};

window.onload = function() {
    removeRedundantTabs();
    higlightSelectedFilters();
};

