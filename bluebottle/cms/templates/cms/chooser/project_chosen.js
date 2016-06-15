function(modal) {
    modal.respond('projectChosen', {{ project|safe }});
    modal.close();
}
