# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-27 14:30
from __future__ import unicode_literals

from bluebottle.utils.utils import update_group_permissions
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django_extensions.db.fields


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# bluebottle.wallposts.migrations.0010_auto_20170821_2001
# bluebottle.wallposts.migrations.0012_auto_20170821_2018
# bluebottle.wallposts.migrations.0014_set_owner_permissions

def add_group_permissions1(apps, schema_editor):
    group_perms = {
        'Staff': {
            'perms': (
                'add_reaction', 'change_reaction', 'delete_reaction',
                'add_wallpost', 'change_wallpost', 'delete_wallpost',
                'add_mediawallpost', 'change_mediawallpost', 'delete_mediawallpost',
                'add_textwallpost', 'change_textwallpost', 'delete_textwallpost',
                'add_systemwallpost', 'change_systemwallpost',
                'delete_systemwallpost',
                'add_mediawallpostphoto', 'change_mediawallpostphoto',
                'delete_mediawallpostphoto',
            )
        },
        'Anonymous': {
            'perms': ('api_read_mediawallpost',)
        },
        'Authenticated': {
            'perms': (
                'api_read_mediawallpost', 'api_add_mediawallpost', 'api_change_mediawallpost', 'api_delete_mediawallpost',
                'api_read_textwallpost', 'api_add_textwallpost', 'api_change_textwallpost', 'api_delete_mediawallpost',
                'api_read_mediawallpostphoto', 'api_add_mediawallpostphoto', 'api_change_mediawallpostphoto',
            )
        }
    }

    update_group_permissions('wallposts', group_perms, apps)


def add_group_permissions2(apps, schema_editor):

    group_perms = {
        'Anonymous': {
            'perms': (
                'api_read_wallpost','api_change_wallpost',
                'api_add_wallpost', 'api_delete_wallpost',
            )
        },
        'Authenticated': {
            'perms': (
                'api_read_wallpost','api_change_wallpost',
                'api_add_wallpost', 'api_delete_wallpost',
            )
        }
    }

    update_group_permissions('wallposts', group_perms, apps)


def add_group_permissions3(apps, schema_editor):
    group_perms = {
        'Anonymous': {
            'perms': (
                'api_read_reaction', 'api_add_reaction',
                'api_change_reaction', 'api_delete_reaction',
            )
        },
        'Authenticated': {
            'perms': (
                'api_read_reaction', 'api_add_reaction',
                'api_change_reaction', 'api_delete_reaction',
            )
        }
    }

    update_group_permissions('wallposts', group_perms, apps)


def set_owner_permissions(apps, schema_editor):
    group_perms = {
        'Anonymous': {
            'perms': ('api_read_mediawallpost',)
        },
        'Authenticated': {
            'perms': (
                'api_read_own_mediawallpost', 'api_change_own_mediawallpost', 'api_delete_own_mediawallpost',
                'api_read_own_textwallpost', 'api_change_own_textwallpost', 'api_delete_own_textwallpost',
                'api_read_own_mediawallpostphoto', 'api_change_own_mediawallpostphoto', 'api_delete_own_mediawallpostphoto',
                'api_read_own_reaction', 'api_change_own_reaction', 'api_delete_own_reaction',
                'api_read_own_wallpost', 'api_change_own_wallpost', 'api_delete_own_wallpost',

            )
        }
    }

    update_group_permissions('wallposts', group_perms, apps)

    authenticated = Group.objects.get(name='Authenticated')
    for perm in (
        'api_change_mediawallpost', 'api_delete_mediawallpost', 'api_change_textwallpost',
        'api_delete_textwallpost', 'api_change_mediawallpostphoto', 'api_delete_mediawallpostphoto',
        'api_change_reaction', 'api_delete_reaction',
        'api_change_wallpost', 'api_delete_wallpost'
        ):
        authenticated.permissions.remove(
            Permission.objects.get(
                codename=perm, content_type__app_label='wallposts'
            )
        )


class Migration(migrations.Migration):

    replaces = [(b'wallposts', '0001_initial'), (b'wallposts', '0002_auto_20161115_1601'), (b'wallposts', '0003_mediawallpostphoto_results_page'), (b'wallposts', '0002_auto_20161109_1024'), (b'wallposts', '0004_merge_20170118_1533'), (b'wallposts', '0004_merge_20170106_1627'), (b'wallposts', '0005_merge_20170124_1338'), (b'wallposts', '0006_remove_duplicate_donation_wallposts'), (b'wallposts', '0007_auto_20170821_1459'), (b'wallposts', '0008_add_group_permissions'), (b'wallposts', '0009_auto_20170821_2001'), (b'wallposts', '0010_auto_20170821_2001'), (b'wallposts', '0011_auto_20170821_2018'), (b'wallposts', '0012_auto_20170821_2018'), (b'wallposts', '0013_auto_20170822_1105'), (b'wallposts', '0014_set_owner_permissions'), (b'wallposts', '0015_auto_20171114_1035'), (b'wallposts', '0016_auto_20180508_1512')]

    dependencies = [
        ('donations', '0004_auto_20160523_1525'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaWallpostPhoto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to=b'mediawallpostphotos')),
                ('deleted', models.DateTimeField(blank=True, null=True, verbose_name='deleted')),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='IP address')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mediawallpostphoto_wallpost_photo', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('editor', models.ForeignKey(blank=True, help_text='The last user to edit this wallpost photo.', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='editor')),
            ],
        ),
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=300, verbose_name='reaction text')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='updated')),
                ('deleted', models.DateTimeField(blank=True, null=True, verbose_name='deleted')),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='IP address')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallpost_reactions', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('editor', models.ForeignKey(blank=True, help_text='The last user to edit this reaction.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='editor')),
            ],
            options={
                'ordering': ('created',),
                'verbose_name': 'Reaction',
                'verbose_name_plural': 'Reactions',
            },
        ),
        migrations.CreateModel(
            name='Wallpost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='updated')),
                ('deleted', models.DateTimeField(blank=True, null=True, verbose_name='deleted')),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='IP address')),
                ('object_id', models.PositiveIntegerField(verbose_name='object ID')),
                ('share_with_facebook', models.BooleanField(default=False)),
                ('share_with_twitter', models.BooleanField(default=False)),
                ('share_with_linkedin', models.BooleanField(default=False)),
                ('email_followers', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='MediaWallpost',
            fields=[
                ('wallpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wallposts.Wallpost')),
                ('title', models.CharField(max_length=60)),
                ('text', models.TextField(blank=True, default=b'', max_length=300)),
                ('video_url', models.URLField(blank=True, default=b'', max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('wallposts.wallpost',),
        ),
        migrations.CreateModel(
            name='SystemWallpost',
            fields=[
                ('wallpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wallposts.Wallpost')),
                ('text', models.TextField(blank=True, max_length=300)),
                ('related_id', models.PositiveIntegerField(verbose_name='related ID')),
                ('related_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', verbose_name='related type')),
            ],
            options={
                'abstract': False,
            },
            bases=('wallposts.wallpost',),
        ),
        migrations.CreateModel(
            name='TextWallpost',
            fields=[
                ('wallpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wallposts.Wallpost')),
                ('text', models.TextField(max_length=300)),
            ],
            options={
                'abstract': False,
            },
            bases=('wallposts.wallpost',),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wallpost_wallpost', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_type_set_for_wallpost', to='contenttypes.ContentType', verbose_name='content type'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='donation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='donation', to='donations.Donation', verbose_name='Donation'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='editor',
            field=models.ForeignKey(blank=True, help_text='The last user to edit this wallpost.', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='editor'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_wallposts.wallpost_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='reaction',
            name='wallpost',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='wallposts.Wallpost'),
        ),
        migrations.AddField(
            model_name='mediawallpostphoto',
            name='mediawallpost',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='wallposts.MediaWallpost'),
        ),
        migrations.AlterModelOptions(
            name='reaction',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'verbose_name': 'Reaction', 'verbose_name_plural': 'Reactions'},
        ),
        migrations.AlterModelOptions(
            name='wallpost',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',)},
        ),
        migrations.AlterModelManagers(
            name='mediawallpost',
            managers=[
                ('objects_with_deleted', django.db.models.manager.Manager()),
                ('base_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='reaction',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('objects_with_deleted', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='systemwallpost',
            managers=[
                ('objects_with_deleted', django.db.models.manager.Manager()),
                ('base_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='textwallpost',
            managers=[
                ('objects_with_deleted', django.db.models.manager.Manager()),
                ('base_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='wallpost',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('objects_with_deleted', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='mediawallpostphoto',
            name='results_page',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterModelOptions(
            name='reaction',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'verbose_name': 'Reaction', 'verbose_name_plural': 'Reactions'},
        ),
        migrations.AlterModelOptions(
            name='wallpost',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',)},
        ),
        migrations.AlterModelManagers(
            name='reaction',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('objects_with_deleted', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='wallpost',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('objects_with_deleted', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelOptions(
            name='mediawallpost',
            options={'permissions': (('api_read_textwallpost', 'Can view text wallposts through the API'), ('api_add_textwallpost', 'Can add text wallposts through the API'), ('api_change_textwallpost', 'Can change text wallposts through the API'), ('api_delete_textwallpost', 'Can delete text wallposts through the API'), ('api_read_mediawallpost', 'Can view media wallposts through the API'), ('api_add_mediawallpost', 'Can add media wallposts through the API'), ('api_change_mediawallpost', 'Can change media wallposts through the API'), ('api_delete_mediawallpost', 'Can delete media wallposts through the API'), ('api_read_mediawallpostphoto', 'Can view media wallpost photos through the API'), ('api_add_mediawallpostphoto', 'Can add media wallpost photos through the API'), ('api_change_mediawallpostphoto', 'Can change media wallpost photos through the API'), ('api_delete_mediawallpostphoto', 'Can delete media wallpost photos through the API'))},
        ),
        migrations.RunPython(
            add_group_permissions1,
        ),
        migrations.AlterModelOptions(
            name='wallpost',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'permissions': (('api_read_wallpost', 'Can view wallposts through the API'), ('api_add_wallpost', 'Can add wallposts through the API'), ('api_change_wallpost', 'Can wallposts documents through the API'), ('api_delete_wallpost', 'Can wallposts documents through the API'))},
        ),
        migrations.RunPython(
            add_group_permissions2,
        ),
        migrations.AlterModelOptions(
            name='reaction',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'permissions': (('api_read_reaction', 'Can view reactions through the API'), ('api_add_reaction', 'Can add reactions through the API'), ('api_change_reaction', 'Can reactions documents through the API'), ('api_delete_reaction', 'Can reactions documents through the API')), 'verbose_name': 'Reaction', 'verbose_name_plural': 'Reactions'},
        ),
        migrations.RunPython(
            add_group_permissions3,
        ),
        migrations.AlterModelOptions(
            name='mediawallpost',
            options={'permissions': (('api_read_own_textwallpost', 'Can view own text wallposts through the API'), ('api_change_own_textwallpost', 'Can change text wallposts through the API'), ('api_delete_own_textwallpost', 'Can delete own text wallposts through the API'), ('api_read_textwallpost', 'Can view text wallposts through the API'), ('api_add_textwallpost', 'Can add text wallposts through the API'), ('api_change_textwallpost', 'Can change text wallposts through the API'), ('api_delete_textwallpost', 'Can delete text wallposts through the API'), ('api_read_mediawallpost', 'Can view media wallposts through the API'), ('api_add_mediawallpost', 'Can add media wallposts through the API'), ('api_change_mediawallpost', 'Can change media wallposts through the API'), ('api_delete_mediawallpost', 'Can delete media wallposts through the API'), ('api_read_own_mediawallpost', 'Can view own media wallposts through the API'), ('api_change_own_mediawallpost', 'Can change own media wallposts through the API'), ('api_delete_own_mediawallpost', 'Can delete own media wallposts through the API'), ('api_read_mediawallpostphoto', 'Can view media wallpost photos through the API'), ('api_add_mediawallpostphoto', 'Can add media wallpost photos through the API'), ('api_change_mediawallpostphoto', 'Can change media wallpost photos through the API'), ('api_delete_mediawallpostphoto', 'Can delete media wallpost photos through the API'), ('api_read_own_mediawallpostphoto', 'Can view own media wallpost photos through the API'), ('api_change_own_mediawallpostphoto', 'Can change own media wallpost photos through the API'), ('api_delete_own_mediawallpostphoto', 'Can delete own media wallpost photos through the API'))},
        ),
        migrations.AlterModelOptions(
            name='reaction',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'permissions': (('api_read_reaction', 'Can view reactions through the API'), ('api_add_reaction', 'Can add reactions through the API'), ('api_change_reaction', 'Can reactions documents through the API'), ('api_delete_reaction', 'Can reactions documents through the API'), ('api_read_own_reaction', 'Can view own reactions through the API'), ('api_add_own_reaction', 'Can add own reactions through the API'), ('api_change_own_reaction', 'Can change own reactions documents through the API'), ('api_delete_own_reaction', 'Can delete own reactions documents through the API')), 'verbose_name': 'Reaction', 'verbose_name_plural': 'Reactions'},
        ),
        migrations.AlterModelOptions(
            name='wallpost',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'permissions': (('api_read_wallpost', 'Can view wallposts through the API'), ('api_add_wallpost', 'Can add wallposts through the API'), ('api_change_wallpost', 'Can wallposts documents through the API'), ('api_delete_wallpost', 'Can wallposts documents through the API'), ('api_read_own_wallpost', 'Can view own wallposts through the API'), ('api_change_own_wallpost', 'Can own wallposts documents through the API'), ('api_delete_own_wallpost', 'Can own wallposts documents through the API'))},
        ),
        migrations.RunPython(
            set_owner_permissions
        ),
        migrations.AlterModelOptions(
            name='mediawallpost',
            options={'permissions': (('api_read_own_textwallpost', 'Can view own text wallposts through the API'), ('api_add_own_textwallpost', 'Can add own text wallposts through the API'), ('api_change_own_textwallpost', 'Can change text wallposts through the API'), ('api_delete_own_textwallpost', 'Can delete own text wallposts through the API'), ('api_read_textwallpost', 'Can view text wallposts through the API'), ('api_add_textwallpost', 'Can add text wallposts through the API'), ('api_change_textwallpost', 'Can change text wallposts through the API'), ('api_delete_textwallpost', 'Can delete text wallposts through the API'), ('api_read_mediawallpost', 'Can view media wallposts through the API'), ('api_add_mediawallpost', 'Can add media wallposts through the API'), ('api_change_mediawallpost', 'Can change media wallposts through the API'), ('api_delete_mediawallpost', 'Can delete media wallposts through the API'), ('api_read_own_mediawallpost', 'Can view own media wallposts through the API'), ('api_add_own_mediawallpost', 'Can add own media wallposts through the API'), ('api_change_own_mediawallpost', 'Can change own media wallposts through the API'), ('api_delete_own_mediawallpost', 'Can delete own media wallposts through the API'), ('api_read_mediawallpostphoto', 'Can view media wallpost photos through the API'), ('api_add_mediawallpostphoto', 'Can add media wallpost photos through the API'), ('api_change_mediawallpostphoto', 'Can change media wallpost photos through the API'), ('api_delete_mediawallpostphoto', 'Can delete media wallpost photos through the API'), ('api_read_own_mediawallpostphoto', 'Can view own media wallpost photos through the API'), ('api_add_own_mediawallpostphoto', 'Can add own media wallpost photos through the API'), ('api_change_own_mediawallpostphoto', 'Can change own media wallpost photos through the API'), ('api_delete_own_mediawallpostphoto', 'Can delete own media wallpost photos through the API'))},
        ),
        migrations.AlterModelOptions(
            name='wallpost',
            options={'base_manager_name': 'objects_with_deleted', 'ordering': ('created',), 'permissions': (('api_read_wallpost', 'Can view wallposts through the API'), ('api_add_wallpost', 'Can add wallposts through the API'), ('api_change_wallpost', 'Can wallposts documents through the API'), ('api_delete_wallpost', 'Can wallposts documents through the API'), ('api_read_own_wallpost', 'Can view own wallposts through the API'), ('api_add_own_wallpost', 'Can add own wallposts through the API'), ('api_change_own_wallpost', 'Can own wallposts documents through the API'), ('api_delete_own_wallpost', 'Can own wallposts documents through the API'))},
        ),
        migrations.AlterField(
            model_name='mediawallpost',
            name='text',
            field=models.TextField(blank=True, default=b'', max_length=1000),
        ),
        migrations.AlterField(
            model_name='mediawallpost',
            name='title',
            field=models.CharField(blank=True, default=b'', max_length=60),
        ),
        migrations.AlterField(
            model_name='reaction',
            name='text',
            field=models.TextField(max_length=1000, verbose_name='reaction text'),
        ),
        migrations.AlterField(
            model_name='systemwallpost',
            name='text',
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='textwallpost',
            name='text',
            field=models.TextField(max_length=1000),
        ),
    ]
