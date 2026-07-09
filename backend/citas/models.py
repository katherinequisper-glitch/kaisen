from django.db import models
from django.contrib.auth.models import User

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    duracion_minutos = models.PositiveIntegerField(default=60)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    disponibilidad = models.OneToOneField('Disponibilidad', on_delete=models.PROTECT, related_name='cita')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.servicio.nombre} - {self.fecha} {self.hora}"

class Disponibilidad(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='disponibilidades')
    fecha = models.DateField()
    hora = models.TimeField()
    ocupado = models.BooleanField(default=False)

    class Meta:
        unique_together = ('servicio', 'fecha', 'hora')
        ordering = ['fecha', 'hora']

    def __str__(self):
        estado = "Ocupado" if self.ocupado else "Libre"
        return f"{self.servicio.nombre} - {self.fecha} {self.hora} ({estado})"