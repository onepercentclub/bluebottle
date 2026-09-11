function removeRedundantTabs() {
  var t = 0;
  django
    .jQuery('.changeform-tabs-item:contains("General")')
    .each(function(index, tab) {
      t++;
      if (t > 1) {
        tab.remove();
      }
    });
}

function removeFluentEditorTabs() {
  // Content-item and placeholder inlines are managed by fluent-contents, not Jet tabs.
  var $container = django.jQuery('#content-main > form > div');
  $container.find('> .inline-contentitem-group, > .inline-placeholder-group').each(function() {
    django.jQuery(this).attr('class').split(/\s+/).forEach(function(className) {
      if (className.match(/^inline_\d+$/)) {
        django.jQuery(
          '.changeform-tabs-item-link[href="#/tab/' + className + '/"]'
        ).closest('.changeform-tabs-item').remove();
      }
    });
  });
}

function addHashToInlinePaginator() {
  // Make sure nested inline paginator links to the same inline tab
  django.jQuery(".paginator a").each(function(index, btn) {
    if (btn.href) {
      btn.href = btn.href.split("#")[0];
      btn.href += document.location.hash;
    }
  });
}

function replaceInlineActivityAddButton() {
  django.jQuery("#activities-group .add-row a").unbind();
  django.jQuery("#activities-group .add-row a").click(function(e) {
    e.preventDefault();
    var path = document.location.pathname;
    path = path.replace(
      "initiatives/initiative/",
      "activities/activity/add/?initiative="
    );
    path = path.replace("/change/", "");
    document.location.href = path;
  });
}

function toggleDeleteButton() {
  if (window.location.hash.startsWith("#/tab/inline")) {
    django.jQuery(".deletelink").hide();
  } else {
    django.jQuery(".deletelink").show();
  }
}

function hideDeleteButton() {
  toggleDeleteButton();
  django.jQuery(window).on("hashchange", function(e) {
    toggleDeleteButton();
  });
}

function hideInfoBoxLabel() {
  django.jQuery(".inline-description").each(function(index, info) {
    const row = info.parentElement.parentElement;
    row.after(info);
    row.remove();
  });
}


function hideRecurringField() {
  if (django.jQuery("#id_slot_type").val() === "recurring") {
    django.jQuery(".field-duration_period").show()
    django.jQuery(".field-max_iterations").show()
  } else {
    django.jQuery(".field-duration_period").hide()
    django.jQuery(".field-max_iterations").hide()
  }

  django.jQuery("#id_slot_type").change(function(value) {
    if (value.target.value === "recurring") {
      django.jQuery(".field-duration_period").fadeIn()
      django.jQuery(".field-max_iterations").fadeIn()
    } else {
      django.jQuery(".field-duration_period").fadeOut()
      django.jQuery(".field-max_iterations").fadeOut()
    }

  })
}


function fixMapboxWidget() {
  let map = document.querySelector('#position-map-elem');
  window.dispatchEvent(new Event("resize"));
}


function tabContentHasErrors($content) {
  return (
    $content.find('.form-row.errors, .row-form-errors, .errorlist').length > 0
  );
}

function revealChangeformTabErrors() {
  var $changeform = django.jQuery('.change-form');
  if (!$changeform.length) {
    return;
  }

  var $container = $changeform.find('#content-main > form > div');
  var $wrappers = $container.find('> .module, > .inline-group');
  var $tabItems = $changeform.find('.changeform-tabs-item');
  var firstErrorHref = null;

  $tabItems.each(function() {
    var $tabItem = django.jQuery(this);
    var href = $tabItem.find('.changeform-tabs-item-link').attr('href') || '';
    var match = href.match(/#\/tab\/([^/]+)\//);
    if (!match) {
      return;
    }
    var $content = $wrappers.filter('.' + match[1]);
    if (tabContentHasErrors($content)) {
      $tabItem.addClass('errors');
      if (!firstErrorHref) {
        firstErrorHref = href;
      }
    }
  });

  if (!firstErrorHref || $tabItems.filter('.selected').hasClass('errors')) {
    return;
  }

  var selector = firstErrorHref.match(/#\/tab\/([^/]+)\//)[1];
  $tabItems.removeClass('selected');
  $wrappers.removeClass('selected');
  $tabItems
    .find('.changeform-tabs-item-link[href="' + firstErrorHref + '"]')
    .closest('.changeform-tabs-item')
    .addClass('selected');
  $wrappers.filter('.' + selector).addClass('selected');
  window.location.hash = firstErrorHref;
}

window.onload = function () {
  if (!django.jQuery && jQuery) {
    django.jQuery = jQuery;
  }

  hideRecurringField()
  fixMapboxWidget()
  replaceInlineActivityAddButton();
  removeRedundantTabs();
  removeFluentEditorTabs();
  addHashToInlinePaginator();
  hideInfoBoxLabel();
  revealChangeformTabErrors();
  hideDeleteButton();
  window.onhashchange = addHashToInlinePaginator;
};
