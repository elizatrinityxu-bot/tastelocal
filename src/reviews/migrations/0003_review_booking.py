from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_booking_status_expand'),
        ('reviews', '0002_review_is_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='booking',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='review',
                to='bookings.booking',
            ),
        ),
        migrations.AddConstraint(
            model_name='review',
            constraint=models.UniqueConstraint(
                condition=models.Q(booking__isnull=False),
                fields=['tourist', 'booking'],
                name='unique_review_per_booking',
            ),
        ),
    ]
