# Generated by Django 2.1.12 on 2019-10-21 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EDL', '0002_auto_20191011_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='edlcontextscorecards',
            name='current_corr_mat_df',
            field=models.BinaryField(default=b''),
        ),
    ]
