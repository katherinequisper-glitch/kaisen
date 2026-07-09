from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    MIGRACIÓN 0002 — Cambios NUEVOS que no existían en producción:
      1. Agrega columna `presencial` a la tabla citas_servicio
      2. Crea la tabla citas_perfil (modelo Perfil con is_premium)

    Esta migración SÍ se aplica normalmente (no fake):
        python manage.py migrate citas 0002
    """

    dependencies = [
        ('citas', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # ── 1. Nuevo campo en Servicio ────────────────────────────────
        migrations.AddField(
            model_name='servicio',
            name='presencial',
            field=models.BooleanField(
                default=False,
                help_text='Si es True, solo usuarios Premium pueden reservarlo.',
            ),
        ),

        # ── 2. Nueva tabla Perfil ─────────────────────────────────────
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_premium', models.BooleanField(default=False)),
                ('creado_en',  models.DateTimeField(auto_now_add=True)),
                ('usuario',    models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='perfil',
                    to='auth.user',
                )),
            ],
        ),
    ]
