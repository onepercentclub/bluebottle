// Ensure qunit doesn't try to auto start tests before Ember/App is ready
QUnit.config.autostart = false;

document.write('<div id="ember-testing-container"><div id="ember-testing"></div></div>');

App.Store = DS.Store.extend({
  adapter: DS.FixtureAdapter.extend({
    queryFixtures: function(fixtures, query, type) {
      // console.log(query);
      // console.log(type);
      return fixtures.filter(function(item) {
          for(prop in query) {
              if( item[prop] != query[prop]) {
                  return false;
              }
          }
          return true;
      });
    }
  })
});

App.rootElement = '#ember-testing';
App.setupForTesting();
App.injectTestHelpers();
// Ember.run(App, App.advanceReadiness);

function exists(selector) {
  return !!find(selector).length;
}

function getAssertionMessage(actual, expected, message) {
  return message || QUnit.jsDump.parse(expected) + " expected but was " + QUnit.jsDump.parse(actual);
}

function equal(actual, expected, message) {
  message = getAssertionMessage(actual, expected, message);
  QUnit.equal.call(this, actual, expected, message);
}

function strictEqual(actual, expected, message) {
  message = getAssertionMessage(actual, expected, message);
  QUnit.strictEqual.call(this, actual, expected, message);
}

window.exists = exists;
window.equal = equal;
window.strictEqual = strictEqual;