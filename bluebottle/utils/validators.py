import os

import magic

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from localflavor.be.forms import BEPostalCodeField
from localflavor.ca.forms import CAPostalCodeField
from localflavor.de.forms import DEZipCodeField
from localflavor.fr.forms import FRZipCodeField
from localflavor.nl.forms import NLZipCodeField


mime = magic.Magic(mime=True)

# Can safely add more post code form fields here.
postal_code_mapping = {
    'BE': BEPostalCodeField(),
    'CA': CAPostalCodeField(),
    'DE': DEZipCodeField(),
    'FR': FRZipCodeField(),
    'NL': NLZipCodeField(),
}


def validate_postal_code(value, country_code):
    if country_code in postal_code_mapping:
        field = postal_code_mapping[country_code]
        field.clean(value)


# Taken from django 1.11
# TODO: use normal validator once we have upgraded
class FileExtensionValidator:
    message = _(
        "File extension '%(extension)s' is not allowed. "
        "Allowed extensions are: '%(allowed_extensions)s'."
    )
    code = 'invalid_extension'

    def __init__(self, allowed_extensions=None, message=None, code=None):
        if allowed_extensions is not None:
            allowed_extensions = [allowed_extension.lower() for allowed_extension in allowed_extensions]
        self.allowed_extensions = allowed_extensions
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

    def __call__(self, value):
        extension = os.path.splitext(value.name)[1][1:].lower()
        if self.allowed_extensions is not None and extension not in self.allowed_extensions:
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    'extension': extension,
                    'allowed_extensions': ', '.join(self.allowed_extensions)
                }
            )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.allowed_extensions == other.allowed_extensions and
            self.message == other.message and
            self.code == other.code

        )

    def deconstruct(self):
        return (
            'bluebottle.utils.validators.FileExtensionValidator',
            (
                self.allowed_extensions,
                getattr(self, 'messsage', None),
                getattr(self, 'code', None),
            ),
            {}
        )


class FileMimetypeValidator:
    message = _(
        "Mime type '%(mimetype)s' is not allowed. "
        "Allowed mime-types are: '%(allowed_mimetypes)s'."
    )
    code = 'invalid_mimetype'

    def __init__(self, allowed_mimetypes=None, message=None, code=None):
        if allowed_mimetypes is not None:
            allowed_mimetypes = [allowed_mimetype.lower() for allowed_mimetype in allowed_mimetypes]
        self.allowed_mimetypes = allowed_mimetypes
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

    def __call__(self, value):
        mimetype = mime.from_buffer(value.file.read(1000))
        value.file.seek(0)

        if self.allowed_mimetypes is not None and mimetype not in self.allowed_mimetypes:
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    'mimetype': mimetype,
                    'allowed_mimetypes': ', '.join(self.allowed_mimetypes)
                }
            )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.allowed_mimetypes == other.allowed_mimetypes and
            self.message == other.message and
            self.code == other.code

        )

    def deconstruct(self):
        return (
            'bluebottle.utils.validators.FileMimetypeValidator',
            (
                self.allowed_mimetypes,
                getattr(self, 'messsage', None),
                getattr(self, 'code', None),
            ),
            {}
        )
