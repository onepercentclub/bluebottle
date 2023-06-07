module.exports = function(str) {
    if (window.gettext) {
        return window.gettext(str);
    }
    return str;
};