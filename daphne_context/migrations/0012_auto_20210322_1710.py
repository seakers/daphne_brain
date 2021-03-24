# Generated by Django 3.1.7 on 2021-03-22 22:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('daphne_context', '0011_auto_20201109_1100'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mycroftuser',
            name='id',
        ),
        migrations.AlterField(
            model_name='mycroftuser',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
