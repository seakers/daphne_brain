# Generated by Django 4.1.1 on 2022-10-06 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0027_alter_eosscontext_design_evaluator_instance_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eosscontext',
            name='design_evaluator_instance_count',
            field=models.IntegerField(default=1),
        ),
    ]
