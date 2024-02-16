function removeRedundantTabs() {
  var t = 0;
  if (django && django.jQuery) {
    django
      .jQuery('.changeform-tabs-item:contains("General")')
      .each(function(index, tab) {
        t++;
        if (t > 1) {
          tab.remove();
        }
      });
  }
}

function addHashToInlinePaginator() {
  // Make sure nested inline paginator links to the same inline tab
  jQuery(".paginator a").each(function(index, btn) {
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
  jQuery(".inline-description").each(function(index, info) {
    const row = info.parentElement.parentElement;
    row.after(info);
    row.remove();
  });
}


function hideRecurringField() {
  if (jQuery("#id_slot_type").val() === "recurring") {
    jQuery(".field-duration_period").show()
    jQuery(".field-max_iterations").show()
  } else {
    jQuery(".field-duration_period").hide()
    jQuery(".field-max_iterations").hide()
  }

  jQuery("#id_slot_type").change(function(value) {
    if (value.target.value === "recurring") {
      jQuery(".field-duration_period").fadeIn()
      jQuery(".field-max_iterations").fadeIn()
    } else {
      jQuery(".field-duration_period").fadeOut()
      jQuery(".field-max_iterations").fadeOut()
    }

  })
}


window.onload = function() {
  if (!django.jQuery && jQuery) {
    django.jQuery = jQuery;
  }
  hideRecurringField()
  replaceInlineActivityAddButton();
  removeRedundantTabs();
  addHashToInlinePaginator();
  hideDeleteButton();
  hideInfoBoxLabel();
  window.onhashchange = addHashToInlinePaginator;
};
