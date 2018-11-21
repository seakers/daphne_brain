# Generated by Django 2.1.3 on 2018-11-14 23:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('merge_session', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveContext',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_background_search_feedback', models.BooleanField(default=False)),
                ('check_for_diversity', models.BooleanField(default=True)),
                ('show_arch_suggestions', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='AllowedCommand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command_type', models.CharField(choices=[('engineer', 'Engineer Commands'), ('critic', 'Critic Commands'), ('historian', 'Historian Commands'), ('analyst', 'iFEED Commands'), ('analyst_instruments', 'Instruments Cheatsheet'), ('analyst_instrument_parameters', 'Instrument Parameters Cheatsheet'), ('analyst_measurements', 'Measurements Cheatsheet'), ('analyst_stakeholders', 'Stakeholders Cheatsheet'), ('measurements', 'Historical Measurements Cheatsheet'), ('missions', 'Historical Missions Cheatsheet'), ('technologies', 'Historical Technologies Cheatsheet'), ('objectives', 'Objectives Cheatsheet'), ('space_agencies', 'Space Agencies Cheatsheet')], max_length=40)),
                ('command_descriptor', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voice_answer', models.TextField()),
                ('visual_answer_type', models.TextField()),
                ('visual_answer', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Design',
            fields=[
                ('design_id', models.AutoField(primary_key=True, serialize=False)),
                ('id', models.IntegerField()),
                ('inputs', models.TextField()),
                ('outputs', models.TextField()),
                ('activecontext', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='daphne_API.ActiveContext')),
            ],
        ),
        migrations.CreateModel(
            name='EngineerContext',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vassar_instrument', models.TextField()),
                ('instrument_parameter', models.TextField()),
                ('vassar_measurement', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='EOSSContext',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem', models.CharField(max_length=50)),
                ('dataset_name', models.CharField(max_length=80)),
                ('last_arch_id', models.IntegerField()),
                ('selected_arch_id', models.IntegerField()),
                ('vassar_port', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='UserInformation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('daphne_version', models.CharField(choices=[('EOSS', 'Earth Observation Satellite Systems'), ('EDL', 'Entry, Descent & Landing'), ('AnomalyDetection', 'Anomaly Detection for Astronauts')], max_length=40)),
                ('channel_name', models.CharField(max_length=120)),
                ('session', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='merge_session.MergeSession')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='eosscontext',
            name='user_information',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='daphne_API.UserInformation'),
        ),
        migrations.AddField(
            model_name='engineercontext',
            name='eosscontext',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext'),
        ),
        migrations.AddField(
            model_name='design',
            name='eosscontext',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext'),
        ),
        migrations.AddField(
            model_name='answer',
            name='eosscontext',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext'),
        ),
        migrations.AddField(
            model_name='allowedcommand',
            name='eosscontext',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext'),
        ),
        migrations.AddField(
            model_name='activecontext',
            name='eosscontext',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext'),
        ),
        migrations.AlterUniqueTogether(
            name='userinformation',
            unique_together={('session', 'user')},
        ),
        migrations.AlterUniqueTogether(
            name='design',
            unique_together={('eosscontext', 'activecontext', 'id')},
        ),
    ]
