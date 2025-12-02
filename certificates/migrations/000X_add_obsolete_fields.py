# Generated migration file
# Save as: certificates/migrations/000X_add_obsolete_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0001_initial'),  # Replace with your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='is_obsolete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='certificate',
            name='obsolete_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='certificate',
            name='obsolete_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]