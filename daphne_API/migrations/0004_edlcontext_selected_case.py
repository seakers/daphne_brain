# Generated by Django 2.1.7 on 2019-03-28 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daphne_API', '0003_edlcontext'),
    ]

    operations = [
        migrations.AddField(
            model_name='edlcontext',
            name='selected_case',
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
    ]
