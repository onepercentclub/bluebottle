/**
 * {{localize SomeNumber}} -> 123
 * {{localize SomeNumber "n2"}} -> 123.45
 * https://github.com/jquery/globalize#numbers
 *
 * {{localize SomeDate "D"}} -> Monday, February 20, 2012
 * {{localize SomeDate "MM,YY"}} -> 02, 12
 *
 */
Em.Handlebars.registerBoundHelper('localize', function (value, options) {
    // Unfortunately although this is 'bound' it won't update it since the value doesn't change.


    // If there's no second argument then formatting will be an object. Set it to null instead.
    var formatting = options.hash['formatting'];
    // Check if it's a Ember Data number or a date
    if (Ember.typeOf(value) == 'number') {
        if (!formatting) {
            formatting = 'n0';
        }
        return new Handlebars.SafeString(Globalize.format(value, formatting));
    }
    if (Ember.typeOf(value) == 'date') {
        if (!formatting) {
            formatting = 'd';
        }
        return new Handlebars.SafeString(Globalize.format(value, formatting));
    }

    //Usisng typeof here since false can be safely rendered
    if (Ember.typeOf(value) == 'undefined' || Ember.isNone(value)){
	    return "";
    }
    
    return new Handlebars.SafeString(Globalize.format(value));
});

Em.Handlebars.registerBoundHelper('linebreaks', function(value, options) {
    if(!value) return ''

    var formatting = options.hash['formatting'];
    if (!formatting || formatting == 'br') {
        return new Handlebars.SafeString(value.replace(/\n\r?/g, '<br />'));
    }
    else {
        return new Handlebars.SafeString('<p>' + value.replace(/\n\r?/g, '</p><p>') + '</p>');
    }
});

Ember.Handlebars.registerHelper('ifExpired', function (property, options, scope) {
  var value, self,
      now = new Date();

  if (typeof scope == 'undefined') {
      self = this;
  } else {
      self = scope;
  }
  
  // If context is an ObjectController then property
  // should be found on the associated model
  if (self instanceof Ember.ObjectController) {
      value = Em.get(self, 'model').get(property);
  } else {
      value = Em.get(self, property);
  }

  if (typeof value.getMonth !== 'function') {
    throw new Error('Property is not a date');
  }
 
  if (now < value) {
     return options.inverse(self);      
  }
  else {
     return options.fn(self);
  }
});


Ember.Handlebars.registerHelper('ifNotExpired', function (property, options) {
    var fn = options.fn, inverse = options.inverse;

    options.fn = inverse;
    options.inverse = fn;

    return Ember.Handlebars.helpers.ifExpired(property, options, this);
});

Ember.Handlebars.helper('daysToGoText', function(value, options) {
  var text = '',
      reachedText = gettext('Deadline<br /> reached');
  
  if (typeof value == 'number') {
      if (value > 0) {
          var daysText = gettext('days'),
              dayText = gettext('day'),
              plural = value > 1 ? daysText : dayText,
              supportText = gettext('to support this project');

          text = '<strong>' + value + ' ' + plural + ' left' + '</strong>';
          text += '<br />' + supportText;
      } else {
          text = '<strong class="deadline-reached">' + reachedText + '</strong>';
      }
  }

  return new Handlebars.SafeString(text);
});
// With this helper you can pass a variable that holds the stack you want to render.
Ember.Handlebars.registerHelper('renderFromVariable', function(name, options, contextString){
    if (!contextString) {
        contextString = {};
    }
    Ember.Handlebars.helpers.render.call(this, 'cheetah.menu', contextString, options)
});
