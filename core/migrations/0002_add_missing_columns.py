from django.db import migrations


class Migration(migrations.Migration):
    """Add missing columns that exist in models but not in DB."""
    
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # core_user fields
        migrations.AddField(
            model_name='user',
            name='hourly_rate',
            field=models.DecimalField(decimal_places=2, default=25.0, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='2020-01-01T00:00:00-05:00'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='first_name',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AddField(
            model_name='user',
            name='last_name',
            field=models.CharField(default='', max_length=150),
        ),
    ]