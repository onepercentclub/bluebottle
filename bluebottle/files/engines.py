from sorl.thumbnail.engines.pil_engine import Engine as PILEngine


class Engine(PILEngine):
    def create(self, image, geometry, options):
        """
        Processing conductor, returns the thumbnail as an image engine instance
        """
        image = self.orientation(image, geometry, options)
        image = self.cropbox(image, geometry, options)
        image = self.colorspace(image, geometry, options)
        image = self.remove_border(image, options)
        image = self.scale(image, geometry, options)
        image = self.crop(image, geometry, options)
        image = self.rounded(image, geometry, options)
        image = self.blur(image, geometry, options)
        image = self.padding(image, geometry, options)
        return image
