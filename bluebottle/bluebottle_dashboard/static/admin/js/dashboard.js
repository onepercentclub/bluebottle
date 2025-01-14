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


window.onload = function () {
  if (!django.jQuery && jQuery) {
    django.jQuery = jQuery;
  }
  hideRecurringField()
  fixMapboxWidget()
  replaceInlineActivityAddButton();
  removeRedundantTabs();
  addHashToInlinePaginator();
  hideDeleteButton();
  hideInfoBoxLabel();
  window.onhashchange = addHashToInlinePaginator;
};
