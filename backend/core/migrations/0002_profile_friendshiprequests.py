# Generated by Django 4.1.5 on 2023-01-11 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='friendshipRequests',
            field=models.ManyToManyField(related_name='+', to='core.profile'),
        ),
    ]
