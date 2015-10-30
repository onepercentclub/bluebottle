# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import DataMigration


class Migration(DataMigration):
    depends_on = (('social.apps.django_app.default', '0001_initial'), )

    def forwards(self, orm):
        "Remove all UserAuth objects that have no extra data."
        db.execute(
            "delete from social_auth_usersocialauth where extra_data='{}'"
        )

    def backwards(self, orm):
        "Do nothing: we do not want the empty objects back."

    models = {

    }

    complete_apps = ['social']
    symmetrical = True
