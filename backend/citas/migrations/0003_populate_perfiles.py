from django.db import migrations


def crear_perfiles_faltantes(apps, schema_editor):
    """
    Crea un Perfil (is_premium=False) para cada User que aún no tenga uno.
    Esto cubre a todos los usuarios registrados ANTES de este cambio.
    """
    User   = apps.get_model('auth', 'User')
    Perfil = apps.get_model('citas', 'Perfil')

    creados = 0
    for user in User.objects.all():
        _, fue_creado = Perfil.objects.get_or_create(usuario=user)
        if fue_creado:
            creados += 1

    print(f'\n  ✅ Perfiles creados para {creados} usuario(s) existente(s).')


def revertir_perfiles(apps, schema_editor):
    """Reversión: no borra perfiles para no perder datos."""
    pass


class Migration(migrations.Migration):
    """
    MIGRACIÓN 0003 — Data migration:
    Genera un Perfil (is_premium=False) para cada usuario que ya existía
    en producción antes de que el signal post_save fuera añadido.
    """

    dependencies = [
        ('citas', '0002_add_presencial_perfil'),
    ]

    operations = [
        migrations.RunPython(
            crear_perfiles_faltantes,
            reverse_code=revertir_perfiles,
        ),
    ]
