from wagtail.wagtailimages.blocks import ImageChooserBlock


class CustomImageChooserBlock(ImageChooserBlock):

    def get_prep_value(self, value):
        # the native value (a model instance or None) should serialise to a PK or None
        if value is None:
            return None
        else:
            return value.pk