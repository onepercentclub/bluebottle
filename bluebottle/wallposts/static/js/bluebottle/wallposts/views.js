/*
 Views
 */

App.WallpostTitleView = Em.TextField.extend({
    placeholder: gettext("Title of your wallpost")
});

App.WallpostBodyView = Em.TextArea.extend({
    placeholder: gettext("Body of your wallpost")
});

App.WallpostVideoView = Em.TextField.extend({
    placeholder: gettext("Youtube or Vimeo url")
});



