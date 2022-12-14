# Generated by Django 4.1.3 on 2022-11-27 13:11

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Redditor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name': 'Redditor',
                'verbose_name_plural': 'Redditors',
            },
        ),
        migrations.CreateModel(
            name='Subreddit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name': 'Watched Sub',
                'verbose_name_plural': 'Watched Subs',
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField()),
                ('deleted', models.BooleanField(default=False)),
                ('submission_id', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=256)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.redditor')),
                ('subreddit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot.subreddit')),
            ],
            options={
                'verbose_name': 'Submission',
                'verbose_name_plural': 'Submissions',
            },
        ),
    ]
