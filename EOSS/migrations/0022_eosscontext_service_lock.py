# Generated by Django 4.1.1 on 2022-09-17 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0021_eosscontext_design_evaluator_service_lock_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='eosscontext',
            name='service_lock',
            field=models.BooleanField(default=False),
        ),
    ]