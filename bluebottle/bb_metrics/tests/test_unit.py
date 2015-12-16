from django.test.utils import override_settings
from mock import patch
from mixpanel import Mixpanel

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_metrics.utils import bb_track


@patch.object(Mixpanel, 'track')
class BbMetricsTestCase(BluebottleTestCase):

    def test_tracking_no_title(self, mock_track):
        result = bb_track()
        self.assertEquals(result, False)

    @override_settings(MIXPANEL="")
    def test_tracking_no_key(self, mock_track):
        result = bb_track("Test event")
        self.assertEquals(result, False)

    @override_settings(MIXPANEL="123456789")
    def test_tracking_title(self, mock_track):
        bb_track("Test Event without data")
        mock_track.assert_called_with(None, "Test Event without data", {})

    @override_settings(MIXPANEL="123456789")
    def test_tracking_title_with_data(self, mock_track):
        bb_track("Test Event", {'bla': 'bla'})
        mock_track.assert_called_with(None, "Test Event", {'bla': 'bla'})
