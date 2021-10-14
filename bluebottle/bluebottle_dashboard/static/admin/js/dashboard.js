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
    jQuery('.paginator a').each(function(index, btn){
        if (btn.href) {
            btn.href = btn.href.split('#')[0]
            btn.href += document.location.hash;
        }
    });
}

function replaceInlineActivityAddButton() {
    django.jQuery('#activities-group .add-row a').unbind();
    django.jQuery('#activities-group .add-row a').click(function(e) {
        e.preventDefault();
        var path = document.location.pathname;
        path = path.replace('initiatives/initiative/', 'activities/activity/add/?initiative=');
        path = path.replace('/change/', '');
        document.location.href = path
    });
}

window.onload = function() {
    replaceInlineActivityAddButton();
    removeRedundantTabs();
    addHashToInlinePaginator();
    window.onhashchange = addHashToInlinePaginator;
};
