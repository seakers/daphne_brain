# Generated by Django 2.2.7 on 2019-11-11 23:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daphne_context', '0006_auto_20191005_1508'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='experimentaction',
            name='experimentstage',
        ),
        migrations.RemoveField(
            model_name='experimentcontext',
            name='user_information',
        ),
        migrations.RemoveField(
            model_name='experimentstage',
            name='experimentcontext',
        ),
        migrations.DeleteModel(
            name='AllowedCommand',
        ),
        migrations.DeleteModel(
            name='ExperimentAction',
        ),
        migrations.DeleteModel(
            name='ExperimentContext',
        ),
        migrations.DeleteModel(
            name='ExperimentStage',
        ),
    ]