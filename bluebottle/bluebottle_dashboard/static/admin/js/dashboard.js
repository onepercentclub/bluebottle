function removeRedundantTabs() {
    var t = 0;
    if (django && django.jQuery) {
        django.jQuery('.changeform-tabs-item:contains("General")').each(function(index, tab){
            t++;
            if (t > 1) {
                tab.remove();
            }
        });
    }
}

function addHashToInlinePaginator() {
    // Make sure nested inline paginator links to the same inline tab
    jQuery('.paginator .btn-page').each(function(index, btn){
        if (btn.href) {
            btn.href = btn.href.split('#')[0]
            btn.href += document.location.hash;
        }
    });
}

window.onload = function() {
    removeRedundantTabs();
    addHashToInlinePaginator();
    window.onhashchange = addHashToInlinePaginator;
};
