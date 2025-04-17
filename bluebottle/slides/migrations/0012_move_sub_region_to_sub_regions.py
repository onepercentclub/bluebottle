from django.db import migrations


def move_sub_region_to_sub_regions(apps, schema_editor):
    Slide = apps.get_model("slides", "Slide")

    # Get all slides that have a sub_region set
    slides_with_sub_region = Slide.objects.exclude(sub_region__isnull=True)

    # For each slide, add the sub_region to sub_regions if not already there
    for slide in slides_with_sub_region:
        if slide.sub_region and slide.sub_region not in slide.sub_regions.all():
            slide.sub_regions.add(slide.sub_region)
            slide.save()


class Migration(migrations.Migration):

    dependencies = [
        ("slides", "0011_slide_sub_regions_alter_slide_sub_region_and_more"),
    ]

    operations = [
        migrations.RunPython(move_sub_region_to_sub_regions, migrations.RunPython.noop),
    ]
