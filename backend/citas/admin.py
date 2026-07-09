from django.contrib import admin
from .models import Servicio, Cita, Disponibilidad, Perfil, Tutor


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'activo')
    list_editable = ('activo',)
    search_fields = ('nombre',)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'is_premium', 'creado_en')
    list_editable = ('is_premium',)
    search_fields = ('usuario__username', 'usuario__email')
    list_filter   = ('is_premium',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display      = ('nombre', 'precio', 'duracion_minutos', 'presencial', 'activo')
    list_editable     = ('precio', 'presencial', 'activo')
    list_filter       = ('activo', 'presencial')
    filter_horizontal = ('tutores',)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'servicio', 'tutor', 'fecha', 'hora', 'estado', 'expira_en')
    list_filter   = ('estado', 'fecha')
    search_fields = ('usuario__username', 'servicio__nombre')


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display  = ('servicio', 'tutor', 'fecha', 'hora', 'ocupado')
    list_filter   = ('ocupado', 'servicio', 'tutor')
    list_editable = ('ocupado',)