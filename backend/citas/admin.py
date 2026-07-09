from django.contrib import admin
from .models import Servicio, Cita, Disponibilidad

admin.site.register(Servicio)
admin.site.register(Cita)
admin.site.register(Disponibilidad)