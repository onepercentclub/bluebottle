var $ = require('jquery');
var SideBarApplicationPinning = require('./application-pinning');
var SideBarBookmarks = require('./bookmarks');
var SideBarPopup = require('./popup');

require('perfect-scrollbar/jquery')($);
require('browsernizr/test/touchevents');
require('browsernizr');
require('jquery.cookie');

var SideBar = function($sidebar) {
    this.$sidebar = $sidebar;
};

SideBar.prototype = {
    initScrollBars: function($sidebar) {
        if (!$(document.documentElement).hasClass('touchevents')) {
            $sidebar.find('.sidebar-wrapper').perfectScrollbar();
        }
    },
    initSideBarToggle: function() {
        var toggle = function(e) {
            e.preventDefault();
            this.sideBarToggle();
        };

        $('.sidebar-toggle').on('click', toggle.bind(this));
    },
    sideBarToggle: function() {
        var open = !$(document.body).hasClass('menu-pinned');

        $(document.body).toggleClass('menu-pinned', open);
        this.storePinStatus(open);
    },
    storePinStatus: function(status) {
        $.cookie('sidebar_pinned', status, { expires: 365, path: '/' });
    },
    addToggleButton: function() {
        var $button = $('<span>')
          .addClass('sidebar-container-toggle sidebar-header-menu-icon icon-menu sidebar-toggle');

        $('#container').prepend($button);
    },
    run: function() {
        var $sidebar = this.$sidebar;

        new SideBarApplicationPinning($sidebar).run();
        new SideBarBookmarks($sidebar).run();
        new SideBarPopup($sidebar).run();

        try {
            this.initScrollBars($sidebar);
            this.addToggleButton();
            this.initSideBarToggle();
        } catch (e) {
            console.error(e, e.stack);
        }

        $sidebar.addClass('initialized');
    }
};


$(document).ready(function() {
    $('.sidebar').each(function() {
        new SideBar($(this)).run();
    });
});

module.exports = new SideBar();
