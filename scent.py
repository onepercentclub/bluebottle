from subprocess import call
from sniffer.api import runnable


@runnable
def execute_tests(*args):
    fn = [
        'python', 'manage.py', 'test',
        '--keepdb', '--settings=bluebottle.settings.testing'
    ]
    fn += args[1:]
    return call(fn) == 0
