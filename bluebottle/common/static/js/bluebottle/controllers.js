////
// Standard Tab Controller with: 
//   Save model on exit
//   Status property associated model
//   Model save actions
//
App.StandardTabController = Em.ObjectController.extend(App.ControllerObjectSaveMixin, App.ControllerObjectStatusMixin, App.SaveOnExitMixin, {});

// Extend BB Modal
App.ModalContainerController = BB.ModalContainerController.extend();

