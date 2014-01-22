Dashboard
=========

BlueBottle provides some modules to use with ``django-admin-tools``. However, the admin tools are not enabled by
default.

To enable the dashboard, just follow the standard configuration instructions from the admin tools documentation.

Modules
-------

To use the BlueBottle modules in the dashboard, simply create a custom dashboard and add the modules. In the example
below, we use ``bluebottle.projects.dashboard.ProjectModule`` and ``bluebottle.tasks.dashboard.TaskModule`` to show a
filtered list of objects in the admin::

    from django.utils.translation import ugettext_lazy as _

    from admin_tools.dashboard import Dashboard

    from bluebottle.projects.dashboard import ProjectModule
    from bluebottle.tasks.dashboard import TaskModule

    class CustomIndexDashboard(Dashboard):
        columns = 3

        def init_with_context(self, context):
            self.children.append(ProjectModule(
                title=_('Recently started Projects'),
                filter_kwargs={'status__name': 'new'})
            )
            self.children.append(TaskModule(
                title=_('Recently realised tasks'),
                filter_kwargs={'status': 'realized'})
            )

In your ``settings.py`` file, add where the dashboard can be found::

    ADMIN_TOOLS_INDEX_DASHBOARD = 'my_project.dashboard.CustomIndexDashboard'

