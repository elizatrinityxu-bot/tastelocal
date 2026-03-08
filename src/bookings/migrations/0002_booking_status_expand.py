from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('CONFIRMED', 'Confirmed'),
                    ('CANCELLED', 'Cancelled'),
                    ('CANCELLED_BY_TOURIST', 'Cancelled by Tourist'),
                    ('COMPLETED', 'Completed'),
                    ('EXPIRED', 'Expired'),
                ],
                default='PENDING',
                max_length=20,
            ),
        ),
    ]
