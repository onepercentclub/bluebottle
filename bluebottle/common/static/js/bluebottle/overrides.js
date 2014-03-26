// Updated modal popup function to fix deprecation warning. See:
// https://github.com/emberjs-addons/ember-bootstrap/issues/79#issuecomment-20852844
Bootstrap.ModalPane.reopenClass({
  rootElement: ".ember-application",
  popup: function(options) {
    var modalPane, rootElement;
    if (!options) options = {};
    modalPane = this.create(options);

    if (!modalPane.container && modalPane.get("controller")) {
      modalPane.container = modalPane.get("controller").container;
    }

    rootElement = get(this, 'rootElement');
    modalPane.appendTo(rootElement);
    return modalPane;
  }
});
