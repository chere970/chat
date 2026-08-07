from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_room_phone_number_phoneotp"),
    ]

    operations = [
        migrations.AddField(
            model_name="phoneotp",
            name="verification_id",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AlterField(
            model_name="phoneotp",
            name="code",
            field=models.CharField(blank=True, default="", max_length=6),
        ),
    ]
