# Generated by Django 4.1.2 on 2022-10-13 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arg', '0003_untrackedregion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datapoint',
            name='dp_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='environmentalactivity',
            name='ea_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='region',
            name='region_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='subregion',
            name='subregion_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='untrackedregion',
            name='untrackedregion_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
