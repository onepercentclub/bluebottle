from rest_framework import renderers

from bluebottle.activity_pub.processor import default_context, processor
from bluebottle.activity_pub.utils import camelize


class JSONLDRenderer(renderers.JSONRenderer):
    media_type = 'application/ld+json'
    format = 'application/ld+json'

    def get_context_for_object(self, data):
        """Return appropriate context based on object type and requirements"""
        
        # Check if this is a Place object that needs Schema.org context
        if data.get('_custom_context') == 'place_with_schema':
            return [
                "https://www.w3.org/ns/activitystreams",
                {
                    "schema": "https://schema.org/",
                    "address": "schema:PostalAddress",
                    "geo": "schema:geo"
                }
            ]
        
        return default_context

    def get_enhanced_context(self, data):
        """Get enhanced context that includes Schema.org terms if needed"""
        # Start with default context
        if isinstance(default_context, list):
            base_context = default_context.copy()
        else:
            base_context = [default_context]
        
        # Check if we have any Place objects that need Schema.org context
        if self.has_place_with_schema(data):
            # Add Schema.org context
            schema_context = {
                "schema": "https://schema.org/",
                "address": "schema:PostalAddress",
                "geo": "schema:geo"
            }
            base_context.append(schema_context)
            
        return base_context

    def has_place_with_schema(self, data):
        """Recursively check if data contains any Place objects with schema context"""
        if isinstance(data, dict):
            if data.get('_custom_context') == 'place_with_schema' or data.get('_customContext') == 'place_with_schema':
                return True
            for value in data.values():
                if isinstance(value, (dict, list)) and self.has_place_with_schema(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)) and self.has_place_with_schema(item):
                    return True
        return False

    def remove_custom_context_markers(self, data):
        """Recursively remove _custom_context markers from data"""
        if isinstance(data, dict):
            data.pop('_custom_context', None)
            data.pop('_customContext', None)  # Also remove camelized version
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self.remove_custom_context_markers(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self.remove_custom_context_markers(item)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        camelized = camelize(data, False)

        if "guActivityType" in camelized:
            camelized["gu:activityType"] = camelized.pop("guActivityType")

        # Get enhanced context that includes Schema.org if needed
        context = self.get_enhanced_context(camelized)
        
        # Remove all custom context markers AFTER checking for them
        self.remove_custom_context_markers(camelized)
        
        camelized['@context'] = context
        compacted = processor.compact(camelized, context, {})

        return super().render(compacted, accepted_media_type, renderer_context)
