"""Adiciona campo image_hash ao Item para busca visual."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0001_initial'),
        ('mainpage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='image_hash',
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True),
        ),
    ]
