from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from bluebottle.files.validators import validate_video_file_size


class ValidateVideoFileSizeTestCase(TestCase):
    def test_accepts_small_file(self):
        small = SimpleUploadedFile('clip.mp4', b'x' * 1024)
        validate_video_file_size(small)

    def test_rejects_large_file(self):
        large = SimpleUploadedFile('clip.mp4', b'x' * (10 * 1024 * 1024 + 1))
        with self.assertRaises(ValidationError):
            validate_video_file_size(large)
