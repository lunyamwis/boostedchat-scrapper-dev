# Generated by Django 4.2.9 on 2024-03-15 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0012_alter_instagramuser_account_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leadsource',
            name='criterion',
            field=models.IntegerField(choices=[(0, 'get similar accounts'), (1, 'get followers'), (2, 'get users'), (3, 'get posts with hashtag'), (4, 'interacted with photos'), (5, 'to be enriched from instagram'), (6, 'google maps'), (7, 'urls'), (8, 'apis')], default=0),
        ),
    ]
