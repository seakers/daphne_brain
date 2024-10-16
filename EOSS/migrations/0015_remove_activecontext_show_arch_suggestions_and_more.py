# Generated by Django 4.0.3 on 2022-03-24 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EOSS', '0014_merge_20220315_1705'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activecontext',
            name='show_arch_suggestions',
        ),
        migrations.RemoveField(
            model_name='activecontext',
            name='show_background_search_feedback',
        ),
        migrations.AddField(
            model_name='activecontext',
            name='analyst_suggestions_frequency',
            field=models.IntegerField(default=45),
        ),
        migrations.AddField(
            model_name='activecontext',
            name='engineer_suggestions_frequency',
            field=models.IntegerField(default=3),
        ),
        migrations.AddField(
            model_name='activecontext',
            name='historian_suggestions_frequency',
            field=models.IntegerField(default=3),
        ),
        migrations.AddField(
            model_name='activecontext',
            name='show_analyst_suggestions',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='activecontext',
            name='show_engineer_suggestions',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='activecontext',
            name='show_historian_suggestions',
            field=models.BooleanField(default=True),
        ),
    ]
