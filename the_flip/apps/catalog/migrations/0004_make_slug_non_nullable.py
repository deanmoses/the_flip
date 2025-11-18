# Generated manually on 2025-11-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_populate_slugs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machinemodel',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, unique=True),
        ),
    ]
