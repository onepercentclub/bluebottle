from django.views.decorators.csrf import csrf_protect

import jet.dashboard.views


jet.dashboard.views.add_user_dashboard_module_view = csrf_protect(jet.dashboard.views.add_user_dashboard_module_view)
jet.dashboard.views.remove_dashboard_module_view = csrf_protect(jet.dashboard.views.remove_dashboard_module_view)
jet.dashboard.views.update_dashboard_modules_view = csrf_protect(jet.dashboard.views.update_dashboard_modules_view)
