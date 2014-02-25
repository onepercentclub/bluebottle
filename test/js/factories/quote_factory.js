Factory.define('quote', {
    quote: '',
    user: function() { return attr('userPreview'); },
});