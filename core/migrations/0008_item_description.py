# Generated by Django 3.0.2 on 2020-02-05 11:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_item_discount_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="description",
            field=models.TextField(default="This is description"),
            preserve_default=False,
        ),
    ]
