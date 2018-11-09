# Generated by Django 2.1.3 on 2018-11-09 18:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('daphne_API', '0005_auto_20181109_1158'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voice_answer', models.TextField()),
                ('visual_answer_type', models.TextField()),
                ('visual_answer', models.TextField()),
                ('eosscontext', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext')),
            ],
        ),
        migrations.CreateModel(
            name='Design',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inputs', models.TextField()),
                ('outputs', models.TextField()),
                ('activecontext', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='daphne_API.ActiveContext')),
                ('eosscontext', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='daphne_API.EOSSContext')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='design',
            unique_together={('eosscontext', 'activecontext')},
        ),
    ]
