# Generated by Django 4.1.1 on 2022-09-06 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0017_eosscontext_cluster_arn_eosscontext_cluster_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eosscontext',
            name='cluster_name',
            field=models.TextField(default='daphne-dev-cluster'),
        ),
    ]