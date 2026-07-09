from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    MIGRACIÓN 0001 — Estado original de la tabla payments_pago en producción.
    Aplicar en producción con:
        python manage.py migrate payments 0001 --fake
    """

    initial = True

    dependencies = [
        ('citas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referencia_culqi', models.CharField(max_length=100)),
                ('monto',            models.DecimalField(decimal_places=2, max_digits=8)),
                ('moneda',           models.CharField(default='PEN', max_length=3)),
                ('creado_en',        models.DateTimeField(auto_now_add=True)),
                ('cita',             models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pago',
                    to='citas.cita',
                )),
            ],
        ),
    ]
