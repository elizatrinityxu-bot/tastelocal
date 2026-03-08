from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_booking_status_expand'),
        ('itinerary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='itinerarystop',
            name='booking',
            field=models.OneToOneField(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='itinerary_stop',
                to='bookings.booking',
            ),
        ),
    ]
