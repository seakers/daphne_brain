# Generated by Django 2.2.8 on 2020-02-16 02:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('AT', '0012_auto_20200214_1013'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='atcontext',
            name='current_procedure_step',
        ),
    ]