from setuptest import setuptest


class BlueBottleTestSuite(setuptest.SetupTestSuite):
    """
    Test Suite configuring Django settings and using
    NoseTestSuiteRunner as test runner.
    """

    def __init__(self, *args, **kwargs):
        super(BlueBottleTestSuite, self).__init__(*args, **kwargs)

        from django_nose import NoseTestSuiteRunner
        self.test_runner = NoseTestSuiteRunner(
            verbosity=1,
            interactive=True,
            failfast=False
        )

    def resolve_packages(self):
        """ 
        We only want to test the BlueBottle apps.
        """
        from django.conf import settings

        top_packages = []

        for app in settings.INSTALLED_APPS:
            if 'bluebottle.' in app:
                top_packages.append(app.split('.')[-1])
        print "Importing mail modules in test runner"
        from bluebottle.bb_tasks import taskmail
        from bluebottle.wallposts import mails
        return top_packages
