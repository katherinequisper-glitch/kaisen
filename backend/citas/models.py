from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Perfil(models.Model):
    """Perfil extendido del usuario. Se crea automáticamente al crear un User."""
    usuario    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    is_premium = models.BooleanField(default=False)
    creado_en  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plan = 'Premium' if self.is_premium else 'Gratuito'
        return f"{self.usuario.username} — {plan}"


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea el Perfil automáticamente cuando se crea un nuevo User."""
    if created:
        Perfil.objects.get_or_create(usuario=instance)


class Servicio(models.Model):
    nombre           = models.CharField(max_length=100)
    descripcion      = models.TextField(blank=True)
    duracion_minutos = models.PositiveIntegerField(default=60)
    precio           = models.DecimalField(max_digits=8, decimal_places=2)
    activo           = models.BooleanField(default=True)
    presencial       = models.BooleanField(default=False,
                           help_text='Si es True, solo usuarios Premium pueden reservarlo.')

    def __str__(self):
        modo = 'Presencial' if self.presencial else 'Online'
        return f"{self.nombre} [{modo}]"


class Cita(models.Model):
    ESTADOS = [
        ('pendiente',  'Pendiente de pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada',  'Cancelada'),
    ]

    usuario        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas')
    servicio       = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    disponibilidad = models.OneToOneField('Disponibilidad', on_delete=models.PROTECT, related_name='cita')
    fecha          = models.DateField()
    hora           = models.TimeField()
    estado         = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_en      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.servicio.nombre} - {self.fecha} {self.hora}"


class Disponibilidad(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='disponibilidades')
    fecha    = models.DateField()
    hora     = models.TimeField()
    ocupado  = models.BooleanField(default=False)

    class Meta:
        unique_together = ('servicio', 'fecha', 'hora')
        ordering        = ['fecha', 'hora']

    def __str__(self):
        estado = "Ocupado" if self.ocupado else "Libre"
        return f"{self.servicio.nombre} - {self.fecha} {self.hora} ({estado})"