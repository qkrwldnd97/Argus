# Generated by Django 4.1.2 on 2022-11-04 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arg", "0004_alter_datapoint_value"),
    ]

    operations = [
        migrations.AlterField(
            model_name="region", name="latitude", field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name="region", name="longitude", field=models.FloatField(default=0),
        ),
    ]
