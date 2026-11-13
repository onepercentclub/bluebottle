from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0119_merge_20261112_0952'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='facebookauthentication',
            name='unique_facebook_authentication',
        ),
        migrations.RemoveConstraint(
            model_name='googleauthentication',
            name='unique_google_authentication',
        ),
        migrations.RemoveConstraint(
            model_name='passwordauthentication',
            name='unique_password_authentication',
        ),
        migrations.AddConstraint(
            model_name='facebookauthentication',
            constraint=models.UniqueConstraint(models.Value(True), name='unique_facebookauthentication'),
        ),
        migrations.AddConstraint(
            model_name='googleauthentication',
            constraint=models.UniqueConstraint(models.Value(True), name='unique_googleauthentication'),
        ),
        migrations.AddConstraint(
            model_name='passwordauthentication',
            constraint=models.UniqueConstraint(models.Value(True), name='unique_passwordauthentication'),
        ),
    ]
