# Generated by Django 2.2.8 on 2020-02-12 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AT', '0004_atcontext_current_telemetry_info'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='atcontext',
            name='current_anomaly',
        ),
        migrations.RemoveField(
            model_name='atcontext',
            name='current_telemetry_info',
        ),
        migrations.AddField(
            model_name='atcontext',
            name='recent_anomalies',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='atcontext',
            name='recent_measurements',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='atcontext',
            name='recent_procedures',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='atcontext',
            name='selected_anomalies',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='atcontext',
            name='selected_measurements',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='atcontext',
            name='selected_procedures',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='atcontext',
            name='current_step',
            field=models.TextField(default=''),
        ),
    ]