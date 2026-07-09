from django.db import models
from citas.models import Cita

class Pago(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='pago')
    referencia_culqi = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    moneda = models.CharField(max_length=3, default='PEN')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.referencia_culqi} - {self.monto} {self.moneda}"
