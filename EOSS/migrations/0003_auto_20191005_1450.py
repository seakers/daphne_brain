# Generated by Django 2.1.12 on 2019-10-05 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0002_auto_20191005_1205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engineercontext',
            name='instrument_parameter',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='engineercontext',
            name='vassar_instrument',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='engineercontext',
            name='vassar_measurement',
            field=models.TextField(null=True),
        ),
    ]