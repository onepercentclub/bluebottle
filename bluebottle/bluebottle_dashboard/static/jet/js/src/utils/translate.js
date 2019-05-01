module.exports = function(str) {
    if (window.django == undefined || !window.django.gettext) {
        return str;
    }

    return django.gettext(str);
};
