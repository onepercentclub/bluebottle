from django.core.exceptions import ValidationError
from django.test import TestCase

from bluebottle.auth.password_validation import (
    CommonPasswordValidator,
    CustomMinimumLengthValidator,
    UserAttributeSimilarityValidator,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class PasswordValidationTestCase(TestCase):
    def test_custom_minimum_length_rejects_short_password(self):
        validator = CustomMinimumLengthValidator(min_length=10)
        with self.assertRaises(ValidationError):
            validator.validate('short')

    def test_custom_minimum_length_accepts_long_password(self):
        validator = CustomMinimumLengthValidator(min_length=10)
        validator.validate('longenough1')

    def test_common_password_validator_rejects_common_password(self):
        validator = CommonPasswordValidator()
        validator.passwords = {'password'}
        with self.assertRaises(ValidationError):
            validator.validate('password')

    def test_user_attribute_similarity_rejects_similar_password(self):
        user = BlueBottleUserFactory.build(first_name='Uniquefirstname')
        validator = UserAttributeSimilarityValidator()
        with self.assertRaises(ValidationError):
            validator.validate('uniquefirstname', user=user)

    def test_user_attribute_similarity_skips_without_user(self):
        validator = UserAttributeSimilarityValidator()
        validator.validate('anything', user=None)
