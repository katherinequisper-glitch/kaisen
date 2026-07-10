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
    whatsapp = models.CharField(max_length=20, blank=True,
                   help_text='Número de WhatsApp con código de país, ej: 51987654321 (sin espacios ni +)')

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
    tutores          = models.ManyToManyField(Tutor, through='ServicioTutor', blank=True, related_name='servicios')

    def __str__(self):
        return self.nombre


class ServicioTutor(models.Model):
    """Conecta un tutor con un servicio, indicando si ESA combinación es presencial o virtual."""
    servicio   = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='servicio_tutores')
    tutor      = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='tutor_servicios')
    presencial = models.BooleanField(default=False,
                    help_text='Si es True, esta modalidad de este tutor requiere Plan Premium.')

    class Meta:
        unique_together = ('servicio', 'tutor')

    def __str__(self):
        modo = 'Presencial' if self.presencial else 'Virtual'
        return f"{self.tutor.nombre} — {self.servicio.nombre} ({modo})"


class Disponibilidad(models.Model):
    servicio    = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='disponibilidades')
    tutor       = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True, related_name='disponibilidades')
    fecha       = models.DateField()
    hora        = models.TimeField()
    cupo_maximo = models.PositiveIntegerField(default=1,
                     help_text='Cupo máximo de alumnos. Virtual: hasta 15. Presencial (premium): debe ser 1 (individual).')

    class Meta:
        unique_together = ('servicio', 'tutor', 'fecha', 'hora')
        ordering        = ['fecha', 'hora']

    @property
    def es_presencial(self):
        st = ServicioTutor.objects.filter(servicio=self.servicio, tutor=self.tutor).first()
        return st.presencial if st else False

    @property
    def cupos_ocupados(self):
        return self.citas.filter(estado__in=['pendiente', 'confirmada']).count()

    @property
    def cupos_disponibles(self):
        return max(0, self.cupo_maximo - self.cupos_ocupados)

    def __str__(self):
        tutor_str = f" — {self.tutor.nombre}" if self.tutor else ""
        return f"{self.servicio.nombre}{tutor_str} - {self.fecha} {self.hora} ({self.cupos_disponibles}/{self.cupo_maximo} libres)"

def _expiracion_default():
    return timezone.now() + timedelta(hours=24)


class Cita(models.Model):
    ESTADOS = [
        ('pendiente',  'Pendiente de pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada',  'Cancelada'),
    ]

    usuario          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas')
    servicio         = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    disponibilidad   = models.ForeignKey('Disponibilidad', on_delete=models.PROTECT, related_name='citas')
    tutor            = models.ForeignKey(Tutor, on_delete=models.SET_NULL, null=True, blank=True)
    fecha            = models.DateField()
    hora             = models.TimeField()
    estado           = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_en        = models.DateTimeField(auto_now_add=True)
    expira_en        = models.DateTimeField(default=_expiracion_default,
                          help_text='Si sigue pendiente después de este momento, se cancela automáticamente.')

    # Clases virtuales
    meet_link        = models.URLField(blank=True)
    meet_password    = models.CharField(max_length=20, blank=True)

    # Clases presenciales (premium)
    direccion_alumno = models.CharField(max_length=255, blank=True,
                          help_text='Dirección/zona que el alumno indicó para la tutoría presencial.')

    def __str__(self):
        return f"{self.usuario.username} - {self.servicio.nombre} - {self.fecha} {self.hora}"