function replaceInlineTaskAddButton() {
    django.jQuery('#task_set-group .add-row a').unbind();
    django.jQuery('#task_set-group .add-row a').click(function(e) {
        e.preventDefault();
        var path = document.location.pathname;
        path = path.replace('projects/project/', 'tasks/task/add/?project=');
        path = path.replace('/change/', '');
        document.location.href = path
    });
}

window.onload = function() {
    replaceInlineTaskAddButton();
};