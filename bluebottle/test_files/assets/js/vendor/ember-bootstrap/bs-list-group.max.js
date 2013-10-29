(function() {
  Bootstrap.BsListGroupComponent = Bootstrap.ItemsView.extend({
    tagName: 'ul',
    classNames: ['list-group'],
    itemViewClass: Bootstrap.ItemView.extend(Bootstrap.ItemSelection, {
      classNames: ['list-group-item'],
      template: Ember.Handlebars.compile(['{{#if view.badge}}', '{{bs-badge contentBinding="view.badge"}}', '{{/if}}', '{{#if view.sub}}', '<h4 class="list-group-item-heading">{{view.title}}</h4>', '<p class="list-group-item-text">{{view.sub}}</p>', '{{else}}', '{{view.title}}', '{{/if}}'].join("\n")),
      badge: (function() {
        var content;
        content = this.get('content');
        if (!(Ember.typeOf(content) === 'instance' || Ember.canInvoke(content, 'get'))) {
          return null;
        }
        return content.get('badge');
      }).property('content'),
      sub: (function() {
        var content;
        content = this.get('content');
        if (!(Ember.typeOf(content) === 'instance' || Ember.canInvoke(content, 'get'))) {
          return null;
        }
        return content.get('sub');
      }).property('content')
    })
  });

  Ember.Handlebars.helper('bs-list-group', Bootstrap.BsListGroupComponent);

}).call(this);
