# Generated by Django 3.1.6 on 2021-02-07 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Therapist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('photo_url', models.CharField(max_length=300)),
            ],
            options={
                'db_table': 'therapists',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('therapists', models.ManyToManyField(db_table='therapists_methods', related_name='methods', to='therapists.Therapist')),
            ],
            options={
                'db_table': 'methods',
            },
        ),
    ]