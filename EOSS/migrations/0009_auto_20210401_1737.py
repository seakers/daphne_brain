# Generated by Django 3.1.7 on 2021-04-01 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0008_auto_20210331_1643'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eosscontext',
            name='ga_id',
        ),
        migrations.AddField(
            model_name='eosscontext',
            name='vassar_queue_url',
            field=models.TextField(null=True),
        ),
    ]
