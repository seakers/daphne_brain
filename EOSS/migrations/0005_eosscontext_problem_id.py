# Generated by Django 2.2.11 on 2020-08-05 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0004_eosscontext_ga_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='eosscontext',
            name='problem_id',
            field=models.IntegerField(default=1),
        ),
    ]
