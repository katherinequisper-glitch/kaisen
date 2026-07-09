from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


class Perfil(models.Model):
    usuario    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    is_premium = models.BooleanField(default=False)
    creado_en  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plan = 'Premium' if self.is_premium else 'Gratuito'
        return f"{self.usuario.username} — {plan}"


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(usuario=instance)


class Tutor(models.Model):
    nombre       = models.CharField(max_length=100)
    foto         = models.ImageField(upload_to='tutores/', blank=True, null=True)
    foto_url     = models.URLField(blank=True, help_text='URL externa de la foto (alternativa a ImageField)')
    descripcion  = models.TextField(help_text='Presentacion breve del tutor')
    estudios     = models.TextField(help_text='Grados, instituciones, certificaciones')
    requisitos   = models.TextField(blank=True, help_text='Que debe saber el alumno antes de esta tutoria')
    activo       = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    @property
    def foto_src(self):
        """Devuelve la URL usable de la foto (prioriza foto_url, luego foto)."""
        if self.foto_url:
            return self.foto_url
        if self.foto and self.foto.name:
            return self.foto.url
        return ''


class Servicio(models.Model):
    nombre           = models.CharField(max_length=100)
    descripcion      = models.TextField(blank=True)
    duracion_minutos = models.PositiveIntegerField(default=60)
    precio           = models.DecimalField(max_digits=8, decimal_places=2)
    activo           = models.BooleanField(default=True)
    presencial       = models.BooleanField(default=False,
                           help_text='Si es True, solo usuarios Premium pueden reservarlo.')
    tutores          = models.ManyToManyField(Tutor, blank=True, related_name='servicios')

    def __str__(self):
        modo = 'Presencial' if self.presencial else 'Online'
        return f"{self.nombre} [{modo}]"


class Disponibilidad(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='disponibilidades')
    tutor    = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True, related_name='disponibilidades')
    fecha    = models.DateField()
    hora     = models.TimeField()
    ocupado  = models.BooleanField(default=False)

    class Meta:
        unique_together = ('servicio', 'tutor', 'fecha', 'hora')
        ordering        = ['fecha', 'hora']

    def __str__(self):
        tutor_str = f" — {self.tutor.nombre}" if self.tutor else ""
        estado    = "Ocupado" if self.ocupado else "Libre"
        return f"{self.servicio.nombre}{tutor_str} - {self.fecha} {self.hora} ({estado})"


def _expiracion_default():
    return timezone.now() + timedelta(hours=24)


class Cita(models.Model):
    ESTADOS = [
        ('pendiente',  'Pendiente de pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada',  'Cancelada'),
    ]

    usuario        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas')
    servicio       = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    disponibilidad = models.OneToOneField('Disponibilidad', on_delete=models.PROTECT, related_name='cita')
    tutor          = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True)
    fecha          = models.DateField()
    hora           = models.TimeField()
    estado         = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_en      = models.DateTimeField(auto_now_add=True)
    expira_en      = models.DateTimeField(default=_expiracion_default,
                        help_text='Si sigue pendiente despues de este momento, se cancela automaticamente.')

    def __str__(self):
        return f"{self.usuario.username} - {self.servicio.nombre} - {self.fecha} {self.hora}"