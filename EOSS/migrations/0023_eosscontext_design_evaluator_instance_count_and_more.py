# Generated by Django 4.1.1 on 2022-10-04 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0022_eosscontext_service_lock'),
    ]

    operations = [
        migrations.AddField(
            model_name='eosscontext',
            name='design_evaluator_instance_count',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='eosscontext',
            name='genetic_algorithm_instance_count',
            field=models.IntegerField(default=1),
        ),
    ]
