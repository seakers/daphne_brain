# Generated by Django 2.2.11 on 2020-08-25 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0006_auto_20200805_1710'),
    ]

    operations = [
        migrations.AddField(
            model_name='eosscontext',
            name='group_id',
            field=models.IntegerField(default=1),
        ),
    ]