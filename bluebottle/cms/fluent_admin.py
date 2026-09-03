from fluent_contents import extensions
from fluent_contents.admin.contentitems import BaseContentItemFormSet, BaseContentItemInline
from nested_admin.formsets import NestedBaseGenericInlineFormSetMixin

COPY_FIELDS = (
    "form",
    "raw_id_fields",
    "filter_vertical",
    "filter_horizontal",
    "radio_fields",
    "prepopulated_fields",
    "formfield_overrides",
    "readonly_fields",
)


class NestedContentItemFormSet(NestedBaseGenericInlineFormSetMixin, BaseContentItemFormSet):
    """Nested formset for fluent ContentItems (generic FK) with placeholder save logic."""


def get_cms_content_item_inlines(plugins=None, base=BaseContentItemInline):
    """
    Like fluent_contents.admin.contentitems.get_content_item_inlines, but also
    copies ``inlines`` from the ContentPlugin so nested admin blocks (steps, quotes, …)
    are attached to the generated ContentItem inline classes.
    """
    if plugins is None:
        plugins = extensions.plugin_pool.get_plugins()

    inlines = []
    for plugin in plugins:
        if not isinstance(plugin, extensions.ContentPlugin):
            raise TypeError(
                "get_cms_content_item_inlines() expects ContentPlugin instances, not {}".format(
                    plugin
                )
            )

        content_item_type = plugin.model
        class_name = "%s_AutoInline" % content_item_type.__name__
        attrs = {
            "__module__": plugin.__class__.__module__,
            "model": content_item_type,
            "name": plugin.verbose_name,
            "plugin": plugin,
            "type_name": plugin.type_name,
            "extra_fieldsets": plugin.fieldsets,
            "cp_admin_form_template": plugin.admin_form_template,
            "cp_admin_init_template": plugin.admin_init_template,
        }

        for name in COPY_FIELDS:
            if getattr(plugin, name, None):
                attrs[name] = getattr(plugin, name)

        plugin_inlines = getattr(plugin, "inlines", None)
        if plugin_inlines:
            attrs["inlines"] = plugin_inlines

        inlines.append(type(class_name, (base,), attrs))

    inlines.sort(key=lambda inline: inline.name.lower())
    return inlines
