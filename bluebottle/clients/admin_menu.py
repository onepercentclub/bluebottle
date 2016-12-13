from fluent_dashboard.menu import FluentMenu


class AdminMenu(FluentMenu):

    def init_with_context(self, context):
        """
        Initialize the menu items.
        """
        super(AdminMenu, self).init_with_context(context)
        # Pop 'Bookmarks' and 'Return to site' items from admin menu.
        self.children.pop(1)
        self.children.pop(len(self.children) - 1)
