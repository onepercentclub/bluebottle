function createProjectChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var input = $('#' + id);
    var title = chooserElement.find('.title'); 
    var img = chooserElement.find('img'); 
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            url: window.chooserUrls.projectChooser,
            responses: {
                projectChosen: function(projectData) {
                    input.val(projectData.id);
                    title.text(projectData.title);
                    img.attr('src', projectData.image);
                    chooserElement.removeClass('blank');
                    editLink.attr('href', projectData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
