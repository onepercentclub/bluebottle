function removeRedundantTabs() {
    var t = 0;
    django.jQuery('.changeform-tabs-item:contains("General")').each(function(index, tab){
        t++;
        if (t > 1) {
            tab.remove();
        }
    });
}

window.onload = function() {
    removeRedundantTabs();
};