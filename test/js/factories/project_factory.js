Factory.define('project', {
    // created: Date.now(),
    owner: function() {
        return attr('userPreview');
    },
    slug: 'empire-strikes-back',
    title: 'Empire Strikes Back',
    
    theme: function() {
        return attr('theme');
    }
});

Factory.define('theme', {
    name: 'Science Fiction'
});