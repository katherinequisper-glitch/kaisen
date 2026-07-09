from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    MIGRACIÓN 0001 — Estado original de la BD de producción.
    Describe las tablas que ya existen (Servicio, Disponibilidad, Cita)
    SIN los campos nuevos (presencial, Perfil).

    En producción, aplicar con:
        python manage.py migrate citas 0001 --fake
    Esto registra esta migración como aplicada sin tocar las tablas reales.
    """

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Servicio',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre',           models.CharField(max_length=100)),
                ('descripcion',      models.TextField(blank=True)),
                ('duracion_minutos', models.PositiveIntegerField(default=60)),
                ('precio',           models.DecimalField(decimal_places=2, max_digits=8)),
                ('activo',           models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Disponibilidad',
            fields=[
                ('id',       models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha',    models.DateField()),
                ('hora',     models.TimeField()),
                ('ocupado',  models.BooleanField(default=False)),
                ('servicio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disponibilidades', to='citas.servicio')),
            ],
            options={
                'ordering': ['fecha', 'hora'],
                'unique_together': {('servicio', 'fecha', 'hora')},
            },
        ),
        migrations.CreateModel(
            name='Cita',
            fields=[
                ('id',             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha',          models.DateField()),
                ('hora',           models.TimeField()),
                ('estado',         models.CharField(
                    choices=[('pendiente', 'Pendiente de pago'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada')],
                    default='pendiente', max_length=20,
                )),
                ('creado_en',      models.DateTimeField(auto_now_add=True)),
                ('disponibilidad', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='cita', to='citas.disponibilidad')),
                ('servicio',       models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='citas.servicio')),
                ('usuario',        models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas', to='auth.user')),
            ],
        ),
    ]
