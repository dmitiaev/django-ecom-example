# Generated by Django 3.0.2 on 2020-02-05 11:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_item_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="quantity",
            field=models.IntegerField(default=1),
        ),
    ]
