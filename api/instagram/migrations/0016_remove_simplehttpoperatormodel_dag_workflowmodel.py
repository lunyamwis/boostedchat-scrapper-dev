# Generated by Django 4.2.9 on 2024-03-26 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0015_dagmodel_simplehttpoperatormodel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='simplehttpoperatormodel',
            name='dag',
        ),
        migrations.CreateModel(
            name='WorkflowModel',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True)),
                ('id', models.CharField(db_index=True, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('dag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='instagram.dagmodel')),
                ('simplehttpoperators', models.ManyToManyField(to='instagram.simplehttpoperatormodel')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
