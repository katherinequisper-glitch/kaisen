from django.db import migrations, models
import django.db.models.deletion
import citas.models


class Migration(migrations.Migration):
    """
    0004 — Agrega modelo Tutor, FK tutor a Disponibilidad y Cita,
           M2M tutores en Servicio, y campo expira_en en Cita.
    Aplicar normalmente: python manage.py migrate citas 0004
    """

    dependencies = [
        ('citas', '0003_populate_perfiles'),
    ]

    operations = [
        # ── 1. Crear tabla citas_tutor ─────────────────────────────────
        migrations.CreateModel(
            name='Tutor',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre',      models.CharField(max_length=100)),
                ('foto',        models.ImageField(blank=True, null=True, upload_to='tutores/')),
                ('foto_url',    models.URLField(blank=True, help_text='URL externa de la foto')),
                ('descripcion', models.TextField(help_text='Presentacion breve del tutor')),
                ('estudios',    models.TextField(help_text='Grados, instituciones, certificaciones')),
                ('requisitos',  models.TextField(blank=True, help_text='Que debe saber el alumno')),
                ('activo',      models.BooleanField(default=True)),
            ],
        ),

        # ── 2. M2M Servicio <-> Tutor ──────────────────────────────────
        migrations.AddField(
            model_name='servicio',
            name='tutores',
            field=models.ManyToManyField(blank=True, related_name='servicios', to='citas.tutor'),
        ),

        # ── 3. FK Disponibilidad -> Tutor (nullable) ───────────────────
        migrations.AddField(
            model_name='disponibilidad',
            name='tutor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='disponibilidades',
                to='citas.tutor',
            ),
        ),

        # ── 4. FK Cita -> Tutor (nullable) ────────────────────────────
        migrations.AddField(
            model_name='cita',
            name='tutor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='citas.tutor',
            ),
        ),

        # ── 5. Campo expira_en en Cita ────────────────────────────────
        migrations.AddField(
            model_name='cita',
            name='expira_en',
            field=models.DateTimeField(
                default=citas.models._expiracion_default,
                help_text='Si sigue pendiente despues de este momento, se cancela automaticamente.',
            ),
        ),

        # ── 6. Actualizar unique_together de Disponibilidad ───────────
        migrations.AlterUniqueTogether(
            name='disponibilidad',
            unique_together={('servicio', 'tutor', 'fecha', 'hora')},
        ),
    ]
